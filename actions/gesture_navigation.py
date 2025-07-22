import time
import numpy as np

class NavigationGestureController:
    """
    Controls navigation actions based on hand gesture recognition.
    Uses temporal hand landmark data to detect directional swipes.
    """
    
    def __init__(self, min_velocity=0.3, min_displacement=0.08, cooldown_time=1.0):
        """
        Initialize the navigation gesture controller.
        
        Args:
            min_velocity: Minimum velocity required to trigger a swipe (normalized units/sec)
            min_displacement: Minimum displacement required for a swipe (normalized units)
            cooldown_time: Time in seconds to wait between gestures to avoid multiple triggers
        """
        self.min_velocity = min_velocity
        self.min_displacement = min_displacement
        self.cooldown_time = cooldown_time
        
        # Tracking last gesture to implement cooldown
        self.last_gesture_time = 0
        self.last_gesture = None
        
        # Store navigation state
        self.current_directory = "/"
        self.directory_contents = ["folder1", "folder2", "folder3", "file1.txt", "file2.txt"]
        self.scroll_position = 0
        
    def detect_navigation_gesture(self, camera, hand_idx=0):
        """
        Detect navigation gestures using the hand landmark buffer.
        
        Args:
            camera: Camera instance with landmark buffer
            hand_idx: Hand index to track (default: 0 for first hand)
            
        Returns:
            Detected navigation action or None
        """
        # First check if palm is open
        is_palm_open, confidence = camera.is_palm_open(hand_idx=hand_idx)
        
        if not is_palm_open or confidence < 0.7:
            return None
        
        # Get whole hand motion
        motion = camera.get_whole_hand_motion(hand_idx=hand_idx)
        
        # Check if motion is valid
        if not motion["valid"]:
            return None
            
        # Get current time for cooldown check
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_gesture_time < self.cooldown_time:
            return None
            
        # Extract motion data
        direction = motion["direction"]
        velocity = motion["velocity"]
        
        # Get finger displacements to verify substantial movement
        if "finger_displacements" not in motion:
            return None
            
        # Calculate average displacement across all fingers
        avg_displacement = sum(motion["finger_displacements"].values()) / len(motion["finger_displacements"])
        
        # Check if motion exceeds thresholds
        if velocity < self.min_velocity or avg_displacement < self.min_displacement:
            return None
            
        # Map direction to navigation action
        navigation_action = None
        
        if direction == "left":
            navigation_action = "go_back"  # Go back one directory
        elif direction == "right":
            navigation_action = "enter_folder"  # Enter selected folder
        elif direction == "up":
            navigation_action = "scroll_up"  # Scroll up in the directory view
        elif direction == "down":
            navigation_action = "scroll_down"  # Scroll down in the directory view
            
        # If we have a valid action, update last gesture time and return the action
        if navigation_action:
            self.last_gesture_time = current_time
            self.last_gesture = navigation_action
            
        return navigation_action
        
    def execute_navigation_action(self, action):
        """
        Execute a navigation action.
        
        Args:
            action: Navigation action name
            
        Returns:
            Result message
        """
        if action == "go_back":
            # Simulate going back to parent directory
            if self.current_directory != "/":
                self.current_directory = "/".join(self.current_directory.split("/")[:-2]) + "/"
                if self.current_directory == "":
                    self.current_directory = "/"
                self.scroll_position = 0
            return f"Go back to {self.current_directory}"
            
        elif action == "enter_folder":
            # Simulate entering a folder
            selected_index = min(self.scroll_position, len(self.directory_contents) - 1)
            if selected_index >= 0 and selected_index < len(self.directory_contents):
                selected_item = self.directory_contents[selected_index]
                if not selected_item.endswith(".txt"):  # Simple check for folder
                    self.current_directory += f"{selected_item}/"
                    # In a real app, would update directory_contents here
                    self.scroll_position = 0
                return f"Enter folder {selected_item}"
            return "No folder selected"
            
        elif action == "scroll_up":
            # Scroll up in current view
            self.scroll_position = max(0, self.scroll_position - 1)
            return f"Scroll up to item {self.scroll_position + 1}"
            
        elif action == "scroll_down":
            # Scroll down in current view
            self.scroll_position = min(len(self.directory_contents) - 1, self.scroll_position + 1)
            return f"Scroll down to item {self.scroll_position + 1}"
            
        return "Unknown action"
        
    def get_current_view(self):
        """
        Get the current directory view information.
        
        Returns:
            Dictionary with current navigation state
        """
        return {
            "current_directory": self.current_directory,
            "directory_contents": self.directory_contents,
            "scroll_position": self.scroll_position,
            "selected_item": self.directory_contents[self.scroll_position] if self.directory_contents else None
        }