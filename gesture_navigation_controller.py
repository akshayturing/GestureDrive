# gesture_navigation_controller.py

import os
import pathlib
from pathlib import Path
import time
import math
import threading
from typing import Dict, List, Tuple, Any, Optional

class GestureNavigationController:
    """
    Advanced gesture controller for file system navigation.
    Maps dynamic gestures like swipes to directory traversal actions.
    """
    
    def __init__(self, initial_path: str = None):
        """
        Initialize the gesture navigation controller.
        
        Args:
            initial_path: Starting directory (defaults to current directory)
        """
        # Set initial working directory
        self.current_path = Path(initial_path) if initial_path else Path.cwd()
        if not self.current_path.exists() or not self.current_path.is_dir():
            raise ValueError(f"Invalid directory path: {self.current_path}")
        
        # Actually change the working directory using os.chdir()
        os.chdir(self.current_path)
        
        # Navigation history
        self.history = [self.current_path]
        self.history_position = 0
        
        # Directory content cache
        self.dir_cache = {}
        self.last_refresh_time = 0
        self.cache_lock = threading.Lock()
        
        # Gesture state tracking
        self.gesture_in_progress = False
        self.gesture_start_time = 0
        self.gesture_start_position = None
        self.gesture_path = []
        
        # Gesture thresholds and configuration
        self.swipe_distance_threshold = 0.15  # Minimum distance for swipe (normalized)
        self.swipe_velocity_threshold = 0.5   # Minimum velocity for swipe (units/second)
        self.swipe_max_duration = 1.0         # Maximum duration for swipe gesture (seconds)
        self.gesture_cooldown = 0.8           # Cooldown between gestures (seconds)
        self.last_gesture_time = 0
        
         # Selected item tracking
        self.selected_index = 0
        # Initialize directory listing
        self.refresh_directory()
        
       
        
    def refresh_directory(self) -> List[Dict[str, Any]]:
        """
        Refresh the current directory listing.
        
        Returns:
            List of dictionaries with file/folder information
        """
        with self.cache_lock:
            current_time = time.time()
            
            # Check if we need to refresh the cache
            if (str(self.current_path) not in self.dir_cache or 
                    current_time - self.last_refresh_time > 2.0):
                try:
                    # Get all items in directory
                    items = []
                    for item in self.current_path.iterdir():
                        # Skip hidden files/folders
                        if item.name.startswith('.'):
                            continue
                            
                        # Get item stats
                        try:
                            stats = item.stat()
                            item_info = {
                                'name': item.name,
                                'path': str(item),
                                'is_dir': item.is_dir(),
                                'size': stats.st_size if item.is_file() else 0,
                                'modified': stats.st_mtime,
                                'type': 'directory' if item.is_dir() else self._get_file_type(item)
                            }
                            items.append(item_info)
                        except (PermissionError, OSError):
                            # Skip items we can't access
                            continue
                    
                    # Sort: directories first, then files alphabetically
                    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
                    
                    # Update cache
                    self.dir_cache[str(self.current_path)] = items
                    self.last_refresh_time = current_time
                    
                    # Reset selected index if needed
                    if self.selected_index >= len(items):
                        self.selected_index = 0 if len(items) == 0 else len(items) - 1
                    
                except (PermissionError, OSError) as e:
                    print(f"Error accessing directory {self.current_path}: {e}")
                    return []
            
            return self.dir_cache.get(str(self.current_path), [])
            
    def _get_file_type(self, path: Path) -> str:
        """Determine file type based on extension."""
        if path.is_dir():
            return "directory"
            
        suffix = path.suffix.lower()
        if suffix in ('.jpg', '.jpeg', '.png', '.gif', '.bmp'):
            return "image"
        elif suffix in ('.mp4', '.avi', '.mov', '.mkv'):
            return "video"
        elif suffix in ('.mp3', '.wav', '.ogg', '.flac'):
            return "audio"
        elif suffix in ('.txt', '.md', '.py', '.js', '.html', '.css'):
            return "text"
        return "file"
    
    def get_current_items(self) -> List[Dict[str, Any]]:
        """Get the current directory items."""
        return self.refresh_directory()
        
    def get_current_path(self) -> Path:
        """Get the current working directory."""
        return self.current_path
        
    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected item or None."""
        items = self.get_current_items()
        if not items or self.selected_index >= len(items):
            return None
        return items[self.selected_index]
    
    def navigate_to(self, path: str or Path) -> bool:
        """
        Navigate to a new directory.
        
        Args:
            path: Target directory path
            
        Returns:
            Success status
        """
        target_path = Path(path) if isinstance(path, str) else path
        
        # Verify target exists and is a directory
        if not target_path.exists() or not target_path.is_dir():
            return False
            
        try:
            # Change the working directory using os.chdir()
            os.chdir(target_path)
            self.current_path = target_path
            
            # Update navigation history
            if self.history_position < len(self.history) - 1:
                # If we went back and now navigate somewhere new,
                # truncate the forward history
                self.history = self.history[:self.history_position + 1]
                
            # Add new path to history if it's different
            if self.history[-1] != self.current_path:
                self.history.append(self.current_path)
                self.history_position = len(self.history) - 1
                
            # Reset selection
            self.selected_index = 0
            
            # Force directory refresh
            self.refresh_directory()
            return True
            
        except (PermissionError, OSError) as e:
            print(f"Error navigating to {target_path}: {e}")
            return False
            
    def navigate_up(self) -> bool:
        """Navigate to the parent directory."""
        parent = self.current_path.parent
        
        # Check if already at root
        if parent == self.current_path:
            return False
            
        return self.navigate_to(parent)
        
    def navigate_back(self) -> bool:
        """Navigate back in history."""
        if self.history_position <= 0:
            return False
            
        self.history_position -= 1
        return self.navigate_to(self.history[self.history_position])
        
    def navigate_forward(self) -> bool:
        """Navigate forward in history."""
        if self.history_position >= len(self.history) - 1:
            return False
            
        self.history_position += 1
        return self.navigate_to(self.history[self.history_position])
        
    def select_next(self) -> bool:
        """Select the next item in the current directory."""
        items = self.get_current_items()
        if not items:
            return False
            
        self.selected_index = (self.selected_index + 1) % len(items)
        return True
        
    def select_previous(self) -> bool:
        """Select the previous item in the current directory."""
        items = self.get_current_items()
        if not items:
            return False
            
        self.selected_index = (self.selected_index - 1) % len(items)
        return True
        
    def open_selected(self) -> bool:
        """Open the selected item (enter directory)."""
        selected = self.get_selected_item()
        if not selected or not selected['is_dir']:
            return False
            
        return self.navigate_to(selected['path'])
    
    def start_gesture(self, landmark_position: Tuple[float, float, float]) -> None:
        """
        Start tracking a potential gesture.
        
        Args:
            landmark_position: (x, y, z) position of tracking landmark
        """
        current_time = time.time()
        
        # Check if we're still in cooldown from previous gesture
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return
            
        self.gesture_in_progress = True
        self.gesture_start_time = current_time
        self.gesture_start_position = landmark_position
        self.gesture_path = [(landmark_position, current_time)]
        
    def update_gesture(self, landmark_position: Tuple[float, float, float]) -> Optional[str]:
        """
        Update an in-progress gesture with new position.
        
        Args:
            landmark_position: (x, y, z) position of tracking landmark
            
        Returns:
            Recognized gesture if complete, None otherwise
        """
        if not self.gesture_in_progress:
            return None
            
        current_time = time.time()
        
        # Add position to gesture path
        self.gesture_path.append((landmark_position, current_time))
        
        # Check if gesture has been going on too long (cancel if so)
        if current_time - self.gesture_start_time > self.swipe_max_duration:
            self.gesture_in_progress = False
            return None
            
        # Check if we have enough movement for a gesture
        if len(self.gesture_path) >= 5:  # Require at least 5 points for reliable detection
            return self._recognize_gesture()
            
        return None
        
    def end_gesture(self) -> Optional[str]:
        """
        End the current gesture and classify it.
        
        Returns:
            Recognized gesture or None
        """
        if not self.gesture_in_progress or len(self.gesture_path) < 5:
            self.gesture_in_progress = False
            return None
            
        gesture = self._recognize_gesture()
        self.gesture_in_progress = False
        
        if gesture:
            self.last_gesture_time = time.time()
            
        return gesture
        
    def _recognize_gesture(self) -> Optional[str]:
        """
        Analyze the current gesture path and classify it.
        
        Returns:
            The recognized gesture type or None
        """
        # Get start and end positions
        start_pos, start_time = self.gesture_path[0]
        end_pos, end_time = self.gesture_path[-1]
        
        # Calculate displacement
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        
        # Calculate duration and distance
        duration = end_time - start_time
        if duration <= 0:
            return None
            
        # Calculate distance and velocity
        distance = math.sqrt(dx*dx + dy*dy)
        velocity = distance / duration
        
        # Check if movement exceeds minimum thresholds
        if distance < self.swipe_distance_threshold or velocity < self.swipe_velocity_threshold:
            return None
            
        # Determine primary direction
        if abs(dx) > abs(dy):
            # Horizontal swipe
            if dx > 0:
                return "swipe_right"
            else:
                return "swipe_left"
        else:
            # Vertical swipe
            if dy > 0:
                return "swipe_down"
            else:
                return "swipe_up"
    
    def process_gesture_for_navigation(self, gesture: str) -> Dict[str, Any]:
        """
        Process a recognized gesture and execute corresponding navigation.
        
        Args:
            gesture: The recognized gesture string
            
        Returns:
            Dictionary with result information
        """
        result = False
        message = ""
        
        if gesture == "swipe_left":
            # Navigate back in history
            result = self.navigate_back()
            message = "Navigated back" if result else "No previous directory"
                
        elif gesture == "swipe_right":
            # Navigate forward in history
            result = self.navigate_forward()
            message = "Navigated forward" if result else "No next directory"
                
        elif gesture == "swipe_up":
            # Navigate to parent directory
            result = self.navigate_up()
            message = f"Navigated to: {self.current_path}" if result else "Already at root directory"
                
        elif gesture == "swipe_down":
            # Open selected directory
            result = self.open_selected()
            selected = self.get_selected_item()
            if result:
                message = f"Entered: {self.current_path.name}"
            elif selected and not selected['is_dir']:
                message = f"Cannot enter: {selected['name']} (not a directory)"
            else:
                message = "No valid directory selected"
                
        # Return current state and operation result
        return {
            'success': result,
            'message': message,
            'current_directory': str(self.current_path),
            'items': self.get_current_items(),
            'selected_index': self.selected_index,
            'selected_item': self.get_selected_item()
        }