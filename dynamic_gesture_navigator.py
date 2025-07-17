# dynamic_gesture_navigator.py

import cv2
import time
import threading
import math
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from camera import Camera
from gesture_navigation_controller import GestureNavigationController

class DynamicGestureNavigator:
    """
    System for navigating the file system using dynamic gesture recognition.
    Uses motion tracking of hand landmarks to detect swipe gestures.
    """
    
    def __init__(self, camera: Camera, initial_path: str = None):
        """
        Initialize the dynamic gesture navigator.
        
        Args:
            camera: Initialized Camera instance
            initial_path: Starting directory path (optional)
        """
        self.camera = camera
        self.navigator = GestureNavigationController(initial_path)
        
        # Tracking state
        self.tracking_active = False
        self.tracking_landmark_id = 8  # Index fingertip 
        self.tracking_hand_id = 0      # First detected hand
        self.landmark_path = []
        self.max_path_points = 20      # Maximum points to store
        
        # Last recognized gesture
        self.last_gesture = None
        self.last_gesture_time = 0
        
        # State for visualization
        self.show_path = True
        self.path_color = (0, 255, 0)  # Green
        self.path_thickness = 2
        
    def update(self) -> Dict[str, Any]:
        """
        Process the latest frame and update navigation state.
        
        Returns:
            Dictionary with current navigation state
        """
        # Get hand landmarks from camera
        landmarks_data = self.camera.hand_landmarks_data
        
        # Get current time for timing operations
        current_time = time.time()
        
        # Process hand landmarks if available
        if landmarks_data and len(landmarks_data) > self.tracking_hand_id:
            hand_landmarks = landmarks_data[self.tracking_hand_id]
            
            # Extract index fingertip position (landmark 8)
            if self.tracking_landmark_id < len(hand_landmarks.landmark):
                landmark = hand_landmarks.landmark[self.tracking_landmark_id]
                position = (landmark.x, landmark.y, landmark.z)
                
                # Handle gesture tracking based on current state
                if not self.tracking_active:
                    # Start new gesture tracking
                    self.navigator.start_gesture(position)
                    self.tracking_active = True
                    self.landmark_path = [(position, current_time)]
                else:
                    # Continue tracking existing gesture
                    self.landmark_path.append((position, current_time))
                    if len(self.landmark_path) > self.max_path_points:
                        self.landmark_path.pop(0)
                        
                    # Update the gesture with new position
                    gesture = self.navigator.update_gesture(position)
                    if gesture:
                        self.process_recognized_gesture(gesture)
        else:
            # No hand detected, finish any in-progress gesture
            if self.tracking_active:
                gesture = self.navigator.end_gesture()
                if gesture:
                    self.process_recognized_gesture(gesture)
                self.tracking_active = False
        
        # Return current state information
        return {
            'current_directory': str(self.navigator.get_current_path()),
            'items': self.navigator.get_current_items(),
            'selected_index': self.navigator.selected_index,
            'selected_item': self.navigator.get_selected_item(),
            'last_gesture': self.last_gesture,
            'tracking_active': self.tracking_active,
            'landmark_path': self.landmark_path.copy() if self.landmark_path else []
        }
        
    def process_recognized_gesture(self, gesture: str) -> None:
        """
        Process a recognized gesture and update navigation state.
        
        Args:
            gesture: The recognized gesture name
        """
        self.last_gesture = gesture
        self.last_gesture_time = time.time()
        
        # Process the gesture for navigation
        result = self.navigator.process_gesture_for_navigation(gesture)
        print(f"Gesture: {gesture}, Result: {result['message']}")
        
    def draw_visualization(self, frame, state: Dict[str, Any]) -> np.ndarray:
        """
        Draw visualization elements on the frame.
        
        Args:
            frame: OpenCV frame to draw on
            state: Current navigation state
            
        Returns:
            Frame with visualizations added
        """
        # Draw UI elements based on current state
        frame = self._draw_directory_panel(frame, state)
        frame = self._draw_status_bar(frame, state)
        
        # Draw gesture path if enabled
        if self.show_path and state['landmark_path']:
            self._draw_landmark_path(frame, state['landmark_path'])
            
        # Draw gesture indication if recent
        if self.last_gesture and time.time() - self.last_gesture_time < 1.0:
            self._draw_gesture_indicator(frame, self.last_gesture)
            
        return frame
        
    def _draw_landmark_path(self, frame, path_points) -> None:
        """Draw the tracked landmark path on the frame."""
        if not path_points or len(path_points) < 2:
            return
            
        h, w = frame.shape[:2]
        points = []
        
        # Convert normalized coordinates to pixel coordinates
        for point, _ in path_points:
            px = int(point[0] * w)
            py = int(point[1] * h)
            points.append((px, py))
            
        # Draw lines connecting points
        for i in range(1, len(points)):
            cv2.line(frame, points[i-1], points[i], self.path_color, 
                     self.path_thickness)
            
        # Draw a circle at the most recent point
        cv2.circle(frame, points[-1], 5, (255, 0, 0), -1)
        
    def _draw_gesture_indicator(self, frame, gesture: str) -> None:
        """Draw an indicator showing the recognized gesture."""
        h, w = frame.shape[:2]
        
        # Define parameters
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = f"Gesture: {gesture}"
        text_size = cv2.getTextSize(text, font, 1, 2)[0]
        
        # Draw background rectangle
        cv2.rectangle(frame, (w - text_size[0] - 20, 50), 
                      (w - 10, 50 + text_size[1] + 20), (0, 0, 0), -1)
                      
        # Draw text
        cv2.putText(frame, text, (w - text_size[0] - 15, 50 + text_size[1] + 5), 
                    font, 1, (255, 255, 255), 2)
                    
    def _draw_directory_panel(self, frame, state: Dict[str, Any]) -> np.ndarray:
        """Draw the directory contents panel."""
        h, w = frame.shape[:2]
        
        # Panel dimensions
        panel_width = 300
        panel_x = w - panel_width
        
        # Draw panel background
        cv2.rectangle(frame, (panel_x, 0), (w, h), (50, 50, 50), -1)
        
        # Draw current directory
        font = cv2.FONT_HERSHEY_SIMPLEX
        curr_dir = Path(state['current_directory']).name or "/"
        cv2.putText(frame, f"Directory: {curr_dir}", 
                    (panel_x + 10, 30), font, 0.6, (255, 255, 255), 1)
                    
        # Draw parent directory
        parent = Path(state['current_directory']).parent
        parent_name = parent.name or "/"
        cv2.putText(frame, f"Parent: {parent_name}", 
                    (panel_x + 10, 60), font, 0.6, (200, 200, 200), 1)
        
        # Draw horizontal separator
        cv2.line(frame, (panel_x, 70), (w, 70), (100, 100, 100), 1)
        
        # Draw items
        items = state['items']
        selected_idx = state['selected_index']
        
        y_pos = 100
        for i, item in enumerate(items):
            # Skip if we have too many items to display
            if y_pos > h - 50:
                break
                
            # Highlight selected item
            if i == selected_idx:
                cv2.rectangle(frame, (panel_x, y_pos - 15), 
                              (w, y_pos + 15), (0, 100, 0), -1)
                              
            # Draw icon based on item type
            icon = "📁 " if item['is_dir'] else "📄 "
            text_color = (255, 255, 255) if i == selected_idx else (200, 200, 200)
            
            # Draw item name
            name = item['name']
            if len(name) > 25:  # Truncate long names
                name = name[:22] + "..."
            cv2.putText(frame, icon + name, 
                        (panel_x + 10, y_pos), font, 0.5, text_color, 1)
            
            y_pos += 30
            
        # Draw help text at bottom
        cv2.rectangle(frame, (panel_x, h - 120), (w, h), (30, 30, 30), -1)
        cv2.putText(frame, "Swipe Controls:", 
                    (panel_x + 10, h - 100), font, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "← Left: Back", 
                    (panel_x + 10, h - 75), font, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "→ Right: Forward", 
                    (panel_x + 10, h - 55), font, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "↑ Up: Parent Directory", 
                    (panel_x + 10, h - 35), font, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, "↓ Down: Enter Directory", 
                    (panel_x + 10, h - 15), font, 0.5, (200, 200, 200), 1)
        
        return frame
        
    def _draw_status_bar(self, frame, state: Dict[str, Any]) -> np.ndarray:
        """Draw the status bar at the bottom of the frame."""
        h, w = frame.shape[:2]
        panel_width = 300  # Match directory panel width
        
        # Draw status bar background
        cv2.rectangle(frame, (0, h - 30), (w - panel_width, h), (0, 0, 0), -1)
        
        # Draw status text
        font = cv2.FONT_HERSHEY_SIMPLEX
        status = f"Tracking: {'Active' if state['tracking_active'] else 'Inactive'}"
        if self.last_gesture and time.time() - self.last_gesture_time < 2.0:
            status += f" | Last Gesture: {self.last_gesture}"
            
        cv2.putText(frame, status, (10, h - 10), font, 0.5, (200, 200, 200), 1)
        
        return frame
        
    def select_next(self) -> None:
        """Select the next item in the directory."""
        self.navigator.select_next()
        
    def select_previous(self) -> None:
        """Select the previous item in the directory."""
        self.navigator.select_previous()
