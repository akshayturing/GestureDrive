# persistent_gesture_navigator.py

import cv2
import time
import math
import threading
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from directory_state_manager import DirectoryStateManager

class PersistentGestureNavigator:
    """
    Persistent gesture-based file system navigator.
    Maintains directory state across application sessions and
    ensures seamless gesture-driven navigation without context loss.
    """
    
    def __init__(self, camera_instance, initial_path: str = None):
        """
        Initialize the persistent gesture navigator.
        
        Args:
            camera_instance: Instance of the camera class
            initial_path: Starting directory (optional)
        """
        # Store camera instance
        self.camera = camera_instance
        
        # Initialize the directory state manager
        self.state_manager = DirectoryStateManager(
            auto_save=True,
            save_interval=10.0  # Save state every 10 seconds
        )
        
        # If initial path is provided, try to use it
        if initial_path:
            self.state_manager.change_directory(initial_path)
        
        # Current directory items and selection
        self.current_items = []
        self.selected_index = 0
        self._update_from_state()
        
        # Gesture tracking
        self.tracking_active = False
        self.gesture_start_position = None
        self.gesture_path = []
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.8  # seconds
        
        # Visualization settings
        self.show_gesture_path = True
        self.path_color = (0, 255, 0)  # Green
        self.path_thickness = 2
        
        # Update monitoring
        self.last_update_time = 0
        self.update_interval = 1.0  # Check for external changes every second
        
        # Status message for UI
        self.status_message = "Ready for gesture commands"
        self.message_timeout = 0
        
    def _update_from_state(self):
        """Update the navigator from the persistent state."""
        # Get current directory
        self.current_directory = self.state_manager.get_current_directory()
        
        # Get selection index for this directory
        self.selected_index = self.state_manager.get_selection_index()
        
        # Update directory listing
        self._refresh_directory_listing()
    
    def _refresh_directory_listing(self):
        """Refresh the current directory listing."""
        try:
            # List all non-hidden items
            items = []
            for item in self.current_directory.iterdir():
                if item.name.startswith('.'):
                    continue
                    
                try:
                    stats = item.stat()
                    items.append({
                        'name': item.name,
                        'path': str(item),
                        'is_dir': item.is_dir(),
                        'size': stats.st_size if item.is_file() else 0,
                        'modified': stats.st_mtime,
                    })
                except (PermissionError, OSError):
                    # Skip items we can't access
                    continue
                    
            # Sort: directories first, then by name
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            self.current_items = items
            
            # Adjust selection index if it's out of bounds
            if self.selected_index >= len(self.current_items):
                self.selected_index = max(0, len(self.current_items) - 1)
                
            # Save the adjusted index
            self.state_manager.set_selection_index(self.selected_index)
            
        except (PermissionError, OSError) as e:
            self.current_items = []
            self.show_status(f"Error accessing directory: {e}", 3.0)
    
    def start_gesture(self, hand_landmark):
        """
        Start tracking a gesture.
        
        Args:
            hand_landmark: The finger landmark to track (usually index fingertip)
        """
        current_time = time.time()
        
        # Skip if we're in cooldown period
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return
            
        # Extract position
        position = (hand_landmark.x, hand_landmark.y, hand_landmark.z)
        
        # Start tracking
        self.tracking_active = True
        self.gesture_start_position = position
        self.gesture_path = [(position, current_time)]
    
    def update_gesture(self, hand_landmark):
        """
        Update an in-progress gesture.
        
        Args:
            hand_landmark: The finger landmark to track
            
        Returns:
            Recognized gesture if complete, None otherwise
        """
        if not self.tracking_active:
            return None
            
        current_time = time.time()
        
        # Extract position
        position = (hand_landmark.x, hand_landmark.y, hand_landmark.z)
        
        # Add to path
        self.gesture_path.append((position, current_time))
        
        # Check for gesture completion
        if len(self.gesture_path) >= 10:
            gesture = self._recognize_gesture()
            if gesture:
                self._execute_gesture_action(gesture)
                self.tracking_active = False
                self.last_gesture_time = current_time
                return gesture
                
        return None
    
    # def end_gesture(self):
    #     """
    #     End the current gesture and recognize it.
        
    #     Returns:
    #         Recognized gesture or None
    #     """
    #     if not self.tracking_active or len(self.gesture_path) < 5:
    #         self.tracking_active = False
    #         return None
            
    #     gesture = self._recognize_gesture()
    #     if gesture:
    #         self._execute_gesture_action(gesture)
            
    #     self.tracking_active = False
    #     self.last_gesture_time = time.time()
    #     return gesture
    def end_gesture(self):
        """
        End the current gesture and recognize it.
        
        Returns:
            Recognized gesture or None
        """
        if not self.tracking_active or len(self.gesture_path) < 5:
            self.tracking_active = False
            return None
            
        gesture = self._recognize_gesture()
        if gesture:
            self._execute_gesture_action(gesture)
            self.last_recognized_gesture = gesture  # Store for UI feedback
            
        self.tracking_active = False
        self.last_gesture_time = time.time()
        return gesture
    
    def _recognize_gesture(self):
        """
        Analyze motion path to recognize gesture.
        
        Returns:
            Gesture type or None
        """
        # Get first and last point
        first_point, first_time = self.gesture_path[0]
        last_point, last_time = self.gesture_path[-1]
        
        # Calculate displacement
        dx = last_point[0] - first_point[0]
        dy = last_point[1] - first_point[1]
        
        # Calculate time and distance
        dt = last_time - first_time
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Minimum thresholds
        min_distance = 0.15
        min_velocity = 0.5
        
        # Check if gesture meets minimum requirements
        if dt <= 0 or distance < min_distance or distance/dt < min_velocity:
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
    
    # def _execute_gesture_action(self, gesture):
    #     """
    #     Execute file system action based on gesture.
        
    #     Args:
    #         gesture: The recognized gesture
    #     """
    #     result = False
    #     message = ""
        
    #     if gesture == "swipe_left":
    #         # Navigate back
    #         result = self.state_manager.navigate_history(forward=False)
    #         message = "Navigated to previous directory" if result else "No previous directory"
            
    #     elif gesture == "swipe_right":
    #         # Navigate forward
    #         result = self.state_manager.navigate_history(forward=True)
    #         message = "Navigated to next directory" if result else "No next directory"
            
    #     elif gesture == "swipe_up":
    #         # Navigate to parent directory
    #         result = self.state_manager.navigate_up()
    #         message = f"Navigated to parent: {self.state_manager.get_current_directory().name}" if result else "Already at root directory"
            
    #     elif gesture == "swipe_down":
    #         # Open selected directory
    #         selected = self.get_selected_item()
    #         if selected and selected['is_dir']:
    #             result = self.state_manager.change_directory(selected['path'])
    #             message = f"Entered directory: {Path(selected['path']).name}" if result else f"Failed to enter {Path(selected['path']).name}"
    #         else:
    #             message = "Cannot enter: Not a directory or no item selected"
        
    #     # Update our local state from the persistent state
    #     if result:
    #         self._update_from_state()
            
    #     # Show status message
    #     self.show_status(message, 2.0)
        
    #     return result
    
    def _execute_gesture_action(self, gesture):
        """
        Execute file system action based on gesture.
        
        Args:
            gesture: The recognized gesture
            
        Returns:
            Success status and message
        """
        result = False
        message = ""
        
        if gesture == "swipe_left":
            # Go back in history
            result = self.state_manager.navigate_history(forward=False)
            message = "Navigated back" if result else "No previous directory"
            
        elif gesture == "swipe_right":
            # Enter selected directory
            selected = self.get_selected_item()
            if selected and selected['is_dir']:
                result = self.state_manager.change_directory(selected['path'])
                message = f"Entered directory: {Path(selected['path']).name}" if result else f"Failed to enter {Path(selected['path']).name}"
            else:
                message = "Cannot enter: Not a directory or no item selected"
                
        elif gesture == "swipe_up":
            # Navigate to parent directory
            result = self.state_manager.navigate_up()
            message = f"Navigated to parent: {self.state_manager.get_current_directory().name}" if result else "Already at root directory"
            
        elif gesture == "swipe_down":
            # Select next item (scroll down)
            result = self.select_next()
            selected = self.get_selected_item()
            message = f"Selected: {selected['name']}" if selected else "No items to select"
        
        # Update our local state from the persistent state
        if result and (gesture == "swipe_left" or gesture == "swipe_right" or gesture == "swipe_up"):
            self._update_from_state()
            
        # Show status message
        self.show_status(message, 2.0)
        
        return result
    def select_next(self):
        """Select the next item in the directory."""
        if not self.current_items:
            return False
            
        self.selected_index = (self.selected_index + 1) % len(self.current_items)
        self.state_manager.set_selection_index(self.selected_index)
        return True
        
    def select_previous(self):
        """Select the previous item in the directory."""
        if not self.current_items:
            return False
            
        self.selected_index = (self.selected_index - 1) % len(self.current_items)
        self.state_manager.set_selection_index(self.selected_index)
        return True
        
    def get_selected_item(self):
        """Get the currently selected item or None."""
        if not self.current_items or self.selected_index >= len(self.current_items):
            return None
        return self.current_items[self.selected_index]
    
    def check_for_updates(self):
        """Check for external file system changes."""
        current_time = time.time()
        
        # Only check at specified intervals
        if current_time - self.last_update_time < self.update_interval:
            return
            
        self.last_update_time = current_time
        
        # Check if directory still exists
        if not self.current_directory.exists():
            # Directory was deleted, navigate to parent
            parent = self.current_directory.parent
            if parent.exists():
                self.state_manager.change_directory(parent)
                self.show_status(f"Directory no longer exists, navigated to parent", 3.0)
            else:
                # If parent doesn't exist either, go to home
                self.state_manager.change_directory(Path.home())
                self.show_status(f"Directory hierarchy changed, reset to home", 3.0)
            
            self._update_from_state()
            return
            
        # Refresh directory listing to capture external changes
        self._refresh_directory_listing()
    
    def show_status(self, message, duration=2.0):
        """
        Show a status message for a specified duration.
        
        Args:
            message: The message to display
            duration: How long to display the message (seconds)
        """
        self.status_message = message
        self.message_timeout = time.time() + duration
    
    # def update(self):
    #     """
    #     Update the navigator state.
        
    #     Returns:
    #         Current state information dictionary
    #     """
    #     # Check for external file system changes
    #     self.check_for_updates()
        
    #     # Process hand landmarks if available
    #     landmarks_data = self.camera.hand_landmarks_data
    #     if landmarks_data and len(landmarks_data) > 0:
    #         # Use the first hand's index finger tip (landmark 8)
    #         hand_landmarks = landmarks_data[0]
    #         if len(hand_landmarks.landmark) > 8:
    #             # Get index fingertip
    #             landmark = hand_landmarks.landmark[8]
                
    #             if not self.tracking_active:
    #                 self.start_gesture(landmark)
    #             else:
    #                 self.update_gesture(landmark)
    #     elif self.tracking_active:
    #         # No hand visible, end any active gesture
    #         self.end_gesture()
            
    #     # Clear expired status message
    #     if time.time() > self.message_timeout:
    #         self.status_message = "Ready for gesture commands"
            
    #     # Return current state
    #     return {
    #         'current_directory': str(self.current_directory),
    #         'items': self.current_items,
    #         'selected_index': self.selected_index,
    #         'selected_item': self.get_selected_item(),
    #         'tracking_active': self.tracking_active,
    #         'status_message': self.status_message,
    #         'gesture_path': self.gesture_path.copy() if self.tracking_active else [],
    #         'history': self.state_manager.get_history(),
    #         'history_position': self.state_manager.get_history_position(),
    #     }
    def update(self):
        """
        Update the navigator state.
        
        Returns:
            Current state information dictionary
        """
        # Check for external file system changes
        self.check_for_updates()
        
        # Process hand landmarks if available
        landmarks_data = self.camera.hand_landmarks_data
        if landmarks_data and len(landmarks_data) > 0:
            # Use the first hand's index finger tip (landmark 8)
            hand_landmarks = landmarks_data[0]
            if len(hand_landmarks.landmark) > 8:
                # Get index fingertip
                landmark = hand_landmarks.landmark[8]
                
                if not self.tracking_active:
                    # Initialize gesture tracking variables if needed
                    if not hasattr(self, 'last_scroll_time'):
                        self.last_scroll_time = 0
                    self.start_gesture(landmark)
                else:
                    # Check for continuous movement for scrolling when gesture is held
                    self.check_vertical_movement(landmark)
                    
                    # Update gesture for recognition
                    self.update_gesture(landmark)
        elif self.tracking_active:
            # No hand visible, end any active gesture
            self.end_gesture()
            
        # Clear expired status message
        if time.time() > self.message_timeout:
            self.status_message = "Ready for gesture commands"
            
        # Return current state
        return {
            'current_directory': str(self.current_directory),
            'items': self.current_items,
            'selected_index': self.selected_index,
            'selected_item': self.get_selected_item(),
            'tracking_active': self.tracking_active,
            'status_message': self.status_message,
            'gesture_path': self.gesture_path.copy() if self.tracking_active else [],
            'history': self.state_manager.get_history(),
            'history_position': self.state_manager.get_history_position(),
        }
    def draw_gesture_feedback(self, frame, gesture=None):
        """
        Draw visual feedback for the current or recent gesture.
        
        Args:
            frame: Video frame to draw on
            gesture: Current gesture or None
        """
        if not gesture and hasattr(self, 'last_recognized_gesture'):
            gesture = self.last_recognized_gesture
        
        if not gesture or time.time() - self.last_gesture_time > 1.5:
            return frame
            
        h, w = frame.shape[:2]
        
        # Position for gesture indicator
        x, y = 100, 100
        size = 60
        thickness = 2
        color = (0, 255, 0)  # Green
        
        # Draw different arrows based on gesture
        if gesture == "swipe_left":
            # Left arrow
            cv2.arrowedLine(frame, (x + size, y), (x, y), color, thickness, tipLength=0.3)
            cv2.putText(frame, "BACK", (x - 20, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        elif gesture == "swipe_right":
            # Right arrow
            cv2.arrowedLine(frame, (x, y), (x + size, y), color, thickness, tipLength=0.3)
            cv2.putText(frame, "ENTER", (x - 20, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        elif gesture == "swipe_up":
            # Up arrow
            cv2.arrowedLine(frame, (x, y + size), (x, y), color, thickness, tipLength=0.3)
            cv2.putText(frame, "PARENT", (x - 30, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
        elif gesture == "swipe_down":
            # Down arrow
            cv2.arrowedLine(frame, (x, y), (x, y + size), color, thickness, tipLength=0.3)
            cv2.putText(frame, "NEXT", (x - 20, y + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return frame
    def draw_ui(self, frame):
        """
        Draw the UI on the frame.
        
        Args:
            frame: Video frame to draw on
            
        Returns:
            Frame with UI elements added
        """
        h, w = frame.shape[:2]
        
        # Draw directory panel
        panel_width = 300
        panel_x = w - panel_width
        
        # Draw background panel
        cv2.rectangle(frame, (panel_x, 0), (w, h), (40, 40, 40), -1)
        
        # Draw current directory
        font = cv2.FONT_HERSHEY_SIMPLEX
        curr_dir_name = self.current_directory.name or "/"
        parent_dir_name = self.current_directory.parent.name or "/"
        
        cv2.putText(frame, "Current:", (panel_x + 10, 25), font, 0.5, (150, 150, 150), 1)
        cv2.putText(frame, curr_dir_name, (panel_x + 10, 50), font, 0.7, (255, 255, 255), 1)
        
        cv2.putText(frame, "Parent:", (panel_x + 10, 75), font, 0.5, (150, 150, 150), 1)
        cv2.putText(frame, parent_dir_name, (panel_x + 10, 100), font, 0.6, (200, 200, 200), 1)
        
        # Draw separator line
        cv2.line(frame, (panel_x, 110), (w, 110), (70, 70, 70), 1)
        
        # Draw file list with scroll if needed
        list_y_start = 130
        list_y_end = h - 120
        item_height = 25
        
        # Calculate visible range
        visible_count = (list_y_end - list_y_start) // item_height
        total_items = len(self.current_items)
        
        # Calculate starting index for scrolling
        if total_items <= visible_count:
            start_idx = 0
        else:
            # Ensure selected item is visible
            middle = visible_count // 2
            start_idx = max(0, min(self.selected_index - middle, total_items - visible_count))
            
        # Draw items
        for i in range(start_idx, min(start_idx + visible_count, total_items)):
            item = self.current_items[i]
            y_pos = list_y_start + (i - start_idx) * item_height
            
            # Highlight selected item
            if i == self.selected_index:
                cv2.rectangle(frame, (panel_x, y_pos - 12), (w, y_pos + 12), (60, 100, 60), -1)
                
            # Draw icon based on type
            icon = "📁 " if item['is_dir'] else "📄 "
            name = item['name']
            if len(name) > 20:  # Truncate long names
                name = name[:17] + "..."
                
            text_color = (255, 255, 255) if i == self.selected_index else (200, 200, 200)
            cv2.putText(frame, icon + name, (panel_x + 15, y_pos), font, 0.55, text_color, 1)
            
        # Draw scroll indicators if needed
        if start_idx > 0:
            cv2.putText(frame, "▲", (w - 20, list_y_start - 5), font, 0.7, (150, 150, 150), 1)
            
        if start_idx + visible_count < total_items:
            cv2.putText(frame, "▼", (w - 20, list_y_end + 5), font, 0.7, (150, 150, 150), 1)
            
        # Draw help panel        
        help_y = h - 110
        cv2.rectangle(frame, (panel_x, help_y), (w, h), (30, 30, 30), -1)
        cv2.putText(frame, "Gesture Controls:", (panel_x + 10, help_y + 20), font, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, "← Left: Back in History", (panel_x + 15, help_y + 40), font, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "→ Right: Enter Folder", (panel_x + 15, help_y + 60), font, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "↑ Up: Parent Directory", (panel_x + 15, help_y + 80), font, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "↓ Down: Select Next", (panel_x + 15, help_y + 100), font, 0.5, (200, 200, 200), 1)

        # Draw status bar
        status_height = 30
        cv2.rectangle(frame, (0, h - status_height), (panel_x, h), (30, 30, 30), -1)
        cv2.putText(frame, self.status_message, (10, h - 10), font, 0.5, (200, 200, 200), 1)
        
        # Draw gesture path if tracking is active
        if self.show_gesture_path and self.tracking_active and len(self.gesture_path) > 1:
            points = []
            for pos, _ in self.gesture_path:
                x = int(pos[0] * w)
                y = int(pos[1] * h)
                points.append((x, y))
                
            # Draw connecting lines
            for i in range(1, len(points)):
                cv2.line(frame, points[i-1], points[i], self.path_color, self.path_thickness)
                
            # Highlight the most recent point
            cv2.circle(frame, points[-1], 5, (0, 0, 255), -1)
            
        frame = self.draw_gesture_feedback(frame)
        return frame
    
    def shutdown(self):
        """Clean up resources and save state."""
        self.state_manager.save_now()
        self.state_manager.shutdown()

    def select_previous_with_gesture(self):
        """Select the previous item as part of a gesture action."""
        if not self.current_items:
            return False
            
        self.selected_index = (self.selected_index - 1) % len(self.current_items)
        self.state_manager.set_selection_index(self.selected_index)
        selected = self.get_selected_item()
        self.show_status(f"Selected: {selected['name']}" if selected else "No items to select", 1.5)
        return True
    
    def check_vertical_movement(self, landmark):
        """
        Check for vertical movement to enable continuous scrolling.
        
        Args:
            landmark: Current hand landmark
        """
        if not self.tracking_active or len(self.gesture_path) < 3:
            return
            
        # Get current and previous positions
        cur_pos = (landmark.x, landmark.y, landmark.z)
        prev_pos, prev_time = self.gesture_path[-1]
        
        # Calculate vertical movement (normalized)
        dy = cur_pos[1] - prev_pos[1]
        
        # Threshold for movement detection
        threshold = 0.015
        
        # Timing check to avoid too rapid scrolling
        current_time = time.time()
        if current_time - self.last_scroll_time < 0.2:  # Limit to ~5 scrolls per second
            return
            
        if dy > threshold:
            # Downward movement - select next
            self.select_next()
            self.last_scroll_time = current_time
        elif dy < -threshold:
            # Upward movement - select previous
            self.select_previous()
            self.last_scroll_time = current_time