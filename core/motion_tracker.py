# core/motion_tracker.py
import time
import numpy as np
from collections import deque
from typing import Dict, List, Any, Optional, Tuple
import logging

class MotionTracker:
    """
    Refactored motion tracker with simplified detection logic.
    """
    
    # Define motion types for consistent reference
    MOTIONS = {
        "STATIONARY": "stationary",
        "SWIPE_UP": "swipe_up",
        "SWIPE_DOWN": "swipe_down",
        "SWIPE_LEFT": "swipe_left",
        "SWIPE_RIGHT": "swipe_right",
        "CIRCLE": "circle",
        "INSUFFICIENT_DATA": "insufficient_data"
    }
    
    def __init__(self, buffer_size=10):
        self.logger = logging.getLogger("MotionTracker")
        self.buffer_size = buffer_size
        
        # Use numpy arrays for more efficient calculations
        self.position_history = deque(maxlen=buffer_size)
        self.velocity_history = deque(maxlen=buffer_size)
        self.timestamp_history = deque(maxlen=buffer_size)
        
        # Motion state
        self.current_motion = self.MOTIONS["STATIONARY"]
        self.motion_buffer = deque(maxlen=3)  # For temporal smoothing
        
        # Motion gesture labels
        self.motion_labels = {
            self.MOTIONS["SWIPE_UP"]: "Swipe Up",
            self.MOTIONS["SWIPE_DOWN"]: "Swipe Down",
            self.MOTIONS["SWIPE_LEFT"]: "Swipe Left",
            self.MOTIONS["SWIPE_RIGHT"]: "Swipe Right",
            self.MOTIONS["CIRCLE"]: "Circle",
            self.MOTIONS["STATIONARY"]: "Stationary",
            self.MOTIONS["INSUFFICIENT_DATA"]: "Analyzing..."
        }
    
    def add_landmarks(self, hand_landmarks, timestamp=None):
        """
        Add a new set of hand landmarks with timestamp.
        
        Args:
            hand_landmarks: List of MediaPipe hand landmarks
            timestamp: Optional timestamp (uses current time if not provided)
        """
        # Only proceed if we have hand landmarks
        if not hand_landmarks or len(hand_landmarks) == 0:
            return
        
        current_time = timestamp or time.time()
        landmarks = hand_landmarks[0]  # Using first hand for now
        
        # Extract the palm position (using landmark 0 - wrist as reference)
        wrist = landmarks.landmark[0]
        
        # Store the position with timestamp
        self.position_history.append(np.array([wrist.x, wrist.y, wrist.z]))
        self.timestamp_history.append(current_time)
        
        # Calculate velocity if we have at least two positions
        if len(self.position_history) >= 2 and len(self.timestamp_history) >= 2:
            pos_current = self.position_history[-1]
            pos_prev = self.position_history[-2]
            time_delta = self.timestamp_history[-1] - self.timestamp_history[-2]
            
            # Avoid division by zero
            if time_delta > 0.001:
                # Calculate velocity vector
                velocity = (pos_current - pos_prev) / time_delta
                magnitude = np.linalg.norm(velocity[:2])  # 2D magnitude (x,y only)
                
                # Store velocity data
                self.velocity_history.append({
                    'vx': velocity[0],
                    'vy': velocity[1], 
                    'vz': velocity[2],
                    'magnitude': magnitude,
                    'timestamp': current_time
                })
    
    def detect_motion_gesture(self, threshold=0.15) -> str:
        """
        Detect motion-based gestures using velocity history.
        
        Args:
            threshold: Minimum velocity threshold to detect motion
            
        Returns:
            Detected motion type
        """
        # Need at least a few velocity samples
        if len(self.velocity_history) < 2:
            return self.MOTIONS["INSUFFICIENT_DATA"]
        
        # Convert to numpy arrays for efficient calculation
        velocities = list(self.velocity_history)
        
        # Get most recent velocities (last 3 or fewer)
        recent_count = min(3, len(velocities))
        recent_velocities = velocities[-recent_count:]
        
        # Extract velocity components
        vx_values = np.array([v['vx'] for v in recent_velocities])
        vy_values = np.array([v['vy'] for v in recent_velocities])
        magnitudes = np.array([v['magnitude'] for v in recent_velocities])
        
        # Calculate averages
        avg_vx = np.mean(vx_values)
        avg_vy = np.mean(vy_values)
        avg_magnitude = np.mean(magnitudes)
        
        # Only detect gesture if motion is significant
        if avg_magnitude < threshold:
            motion = self.MOTIONS["STATIONARY"]
        else:
            # Determine the primary motion direction
            if abs(avg_vx) > abs(avg_vy):
                # Primarily horizontal motion
                motion = self.MOTIONS["SWIPE_RIGHT"] if avg_vx > 0 else self.MOTIONS["SWIPE_LEFT"]
            else:
                # Primarily vertical motion
                motion = self.MOTIONS["SWIPE_DOWN"] if avg_vy > 0 else self.MOTIONS["SWIPE_UP"]
        
        # Add to motion buffer for temporal smoothing
        self.motion_buffer.append(motion)
        
        # Only update if motion is consistent or significant
        if motion != self.MOTIONS["STATIONARY"]:
            # Count motion types in buffer
            from collections import Counter
            motion_counts = Counter(self.motion_buffer)
            
            # Get most common motion
            if motion_counts:
                most_common = motion_counts.most_common(1)[0]
                if most_common[1] >= 2:  # Require at least 2 occurrences
                    self.current_motion = most_common[0]
        elif all(m == self.MOTIONS["STATIONARY"] for m in self.motion_buffer):
            # Only set to stationary if buffer is full of stationary
            self.current_motion = self.MOTIONS["STATIONARY"]
        
        return self.current_motion
    
    def get_motion_label(self, motion=None) -> str:
        """
        Convert motion type to human-readable label.
        """
        if motion is None:
            motion = self.current_motion
        
        return self.motion_labels.get(motion, "Unknown Motion")
    
    def get_velocity_stats(self) -> Dict[str, float]:
        """
        Get statistics about recent velocity.
        """
        if not self.velocity_history:
            return {
                'avg_magnitude': 0,
                'max_magnitude': 0,
                'direction_x': 0,
                'direction_y': 0
            }
        
        # Use the 3 most recent velocities if available
        recent_count = min(3, len(self.velocity_history))
        recent = list(self.velocity_history)[-recent_count:]
        
        return {
            'avg_magnitude': sum(v['magnitude'] for v in recent) / len(recent),
            'max_magnitude': max(v['magnitude'] for v in recent),
            'direction_x': sum(v['vx'] for v in recent) / len(recent),
            'direction_y': sum(v['vy'] for v in recent) / len(recent)
        }
    
    def is_motion_active(self) -> bool:
        """
        Check if there is currently active motion.
        """
        return self.current_motion != self.MOTIONS["STATIONARY"] and \
               self.current_motion != self.MOTIONS["INSUFFICIENT_DATA"]
    
    def detect_trajectory(self) -> Optional[Dict[str, Any]]:
        """
        Analyze the movement trajectory to detect more complex patterns.
        
        Returns:
            Dictionary with trajectory information or None
        """
        # Need enough position history
        if len(self.position_history) < 5:
            return None
            
        positions = list(self.position_history)
        
        # Convert to numpy array for easier analysis
        trajectory = np.array(positions)
        
        # Get bounding box of the trajectory
        min_x, min_y = np.min(trajectory[:, :2], axis=0)
        max_x, max_y = np.max(trajectory[:, :2], axis=0)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Analyze shape of trajectory
        # Circle detection would need more complex analysis
        # This is a simplified approach
        
        return {
            'width': width,
            'height': height,
            'aspect_ratio': width/height if height > 0 else 0,
            'distance': np.linalg.norm(trajectory[-1] - trajectory[0]),
            'is_circular': False  # Placeholder for more complex detection
        }