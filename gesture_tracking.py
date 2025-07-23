# """
# gesture_tracking.py - Hand landmarks tracking and gesture detection module

# This module provides gesture tracking functionality including:
# - Tracking hand landmarks across multiple frames
# - Calculating motion trajectories and velocities
# - Detecting directional gestures with validation
# - Providing reliable gesture recognition with duration and posture validation
# """

# import math
# import time
# import logging
# from typing import Dict, List, Optional, Tuple, Any
# from collections import deque
# import numpy as np

# class HandLandmarkTracker:
#     """
#     Tracks hand landmarks across frames to detect gestures and validate
#     them based on duration and posture criteria.
#     """
    
#     def __init__(self, buffer_size: int = 10, min_gesture_duration_ms: int = 500):
#         """
#         Initialize the hand landmark tracker.
        
#         Args:
#             buffer_size: Number of frames to keep in history for each landmark
#             min_gesture_duration_ms: Minimum duration for gesture validation in milliseconds
#         """
#         self.logger = logging.getLogger(__name__)
#         self.buffer_size = buffer_size
#         self.min_gesture_duration = min_gesture_duration_ms / 1000.0  # Convert to seconds
        
#         # Track landmarks history for velocity calculation
#         self.landmark_history = {}  # {hand_id: {landmark_id: deque(positions)}}
        
#         # Gesture state tracking
#         self.current_motion_candidate = None
#         self.motion_start_time = 0
#         self.validated_motion = None
        
#         # Debug information
#         self.debug_info = {
#             "last_validation_reason": None,
#             "tracking_duration": 0,
#             "posture_valid": False
#         }
    
#     def add_landmarks(self, multi_hand_landmarks: Any) -> None:
#         """
#         Add new hand landmarks with current timestamp for motion tracking.
        
#         Args:
#             multi_hand_landmarks: MediaPipe hand landmarks results
#         """
#         current_time = time.time()
        
#         for hand_idx, hand_landmarks in enumerate(multi_hand_landmarks):
#             # Create unique key for each hand
#             hand_key = f"hand_{hand_idx}"
            
#             # Initialize if this hand hasn't been seen before
#             if hand_key not in self.landmark_history:
#                 self.landmark_history[hand_key] = {}
            
#             # Process each landmark in the hand
#             for i, landmark in enumerate(hand_landmarks.landmark):
#                 landmark_key = f"landmark_{i}"
                
#                 # Initialize if this landmark hasn't been tracked before
#                 if landmark_key not in self.landmark_history[hand_key]:
#                     self.landmark_history[hand_key][landmark_key] = deque(maxlen=self.buffer_size)
                
#                 # Store the landmark position with timestamp
#                 self.landmark_history[hand_key][landmark_key].append({
#                     'x': landmark.x,
#                     'y': landmark.y,
#                     'z': landmark.z,
#                     'timestamp': current_time
#                 })
    
#     def get_landmark_trajectory(self, hand_idx: int = 0, landmark_idx: int = 8) -> List[Tuple[Dict[str, float], float]]:
#         """
#         Get the trajectory of a specific landmark over time.
#         Default is index fingertip (landmark_idx 8) of first hand.
        
#         Args:
#             hand_idx: Hand index (0 for first detected hand)
#             landmark_idx: Landmark index to track
            
#         Returns:
#             List of (position, timestamp) tuples
#         """
#         hand_key = f"hand_{hand_idx}"
#         landmark_key = f"landmark_{landmark_idx}"
        
#         if (hand_key not in self.landmark_history or
#             landmark_key not in self.landmark_history[hand_key]):
#             return []
        
#         history = self.landmark_history[hand_key][landmark_key]
#         return [(point, point['timestamp']) for point in history]
    
#     def calculate_velocity(self, hand_idx: int = 0, landmark_idx: int = 8) -> Optional[List[Dict[str, float]]]:
#         """
#         Calculate velocity of a landmark between frames.
        
#         Args:
#             hand_idx: Which hand to track (0 for first hand)
#             landmark_idx: Which landmark to track (8 for index fingertip)
            
#         Returns:
#             List of velocity data dictionaries or None if not enough data
#         """
#         trajectory = self.get_landmark_trajectory(hand_idx, landmark_idx)
        
#         if len(trajectory) < 2:
#             return None
        
#         velocities = []
#         for i in range(1, len(trajectory)):
#             curr_point, curr_time = trajectory[i]
#             prev_point, prev_time = trajectory[i-1]
            
#             # Calculate time difference
#             dt = curr_time - prev_time
#             if dt <= 0:
#                 continue
                
#             # Calculate distance moved
#             dx = curr_point['x'] - prev_point['x']
#             dy = curr_point['y'] - prev_point['y']
#             dz = curr_point['z'] - prev_point['z']
            
#             # Calculate velocity components
#             vx = dx / dt
#             vy = dy / dt
#             vz = dz / dt
            
#             # Calculate velocity magnitude
#             v_mag = math.sqrt(vx*vx + vy*vy + vz*vz)
            
#             velocities.append({
#                 'timestamp': curr_time,
#                 'vx': vx, 
#                 'vy': vy, 
#                 'vz': vz,
#                 'magnitude': v_mag
#             })
            
#         return velocities
    
#     def is_valid_hand_posture(self, landmarks) -> bool:
#         """
#         Check if hand posture is valid: all fingers (except thumb) fully extended 
#         and pointing toward camera.
        
#         Args:
#             landmarks: MediaPipe hand landmarks
            
#         Returns:
#             True if posture is valid, False otherwise
#         """
#         # Exit early if no landmarks
#         if not landmarks:
#             self.debug_info["last_validation_reason"] = "No landmarks"
#             return False
        
#         # Finger joints - PIP is Proximal Interphalangeal Joint (middle joint)
#         # DIP is Distal Interphalangeal Joint (joint nearest to fingertip)
#         finger_joints = {
#             'index': {'mcp': 5, 'pip': 6, 'dip': 7, 'tip': 8},
#             'middle': {'mcp': 9, 'pip': 10, 'dip': 11, 'tip': 12},
#             'ring': {'mcp': 13, 'pip': 14, 'dip': 15, 'tip': 16},
#             'pinky': {'mcp': 17, 'pip': 18, 'dip': 19, 'tip': 20}
#         }
        
#         # Check each finger (excluding thumb)
#         all_fingers_extended = True
#         all_fingers_pointing_forward = True
        
#         for finger_name, joints in finger_joints.items():
#             # 1. Check if finger is extended by comparing tip to base distance
#             mcp = landmarks[joints['mcp']]
#             pip = landmarks[joints['pip']]
#             dip = landmarks[joints['dip']]
#             tip = landmarks[joints['tip']]
            
#             # Calculate finger segment lengths
#             mcp_to_pip_length = self._distance_3d(mcp, pip)
#             pip_to_dip_length = self._distance_3d(pip, dip)
#             dip_to_tip_length = self._distance_3d(dip, tip)
            
#             # Calculate direct distance from MCP to tip
#             direct_distance = self._distance_3d(mcp, tip)
            
#             # Sum of finger segment lengths
#             total_finger_length = mcp_to_pip_length + pip_to_dip_length + dip_to_tip_length
            
#             # Finger is considered extended if direct distance is at least 75% of total length
#             extension_ratio = direct_distance / total_finger_length if total_finger_length > 0 else 0
#             is_extended = extension_ratio > 0.75
            
#             # 2. Check if finger is pointing toward camera (z-direction)
#             # Calculate vectors along finger
#             vec_mcp_to_tip = (tip.x - mcp.x, tip.y - mcp.y, tip.z - mcp.z)
            
#             # Normalize the vector
#             magnitude = math.sqrt(vec_mcp_to_tip[0]**2 + vec_mcp_to_tip[1]**2 + vec_mcp_to_tip[2]**2)
#             if magnitude > 0:
#                 vec_norm = (vec_mcp_to_tip[0]/magnitude, vec_mcp_to_tip[1]/magnitude, vec_mcp_to_tip[2]/magnitude)
#             else:
#                 vec_norm = (0, 0, 0)
            
#             # Check z component - negative means pointing toward camera in MediaPipe coordinates
#             # The z component should be significant (at least 0.5 in magnitude) when pointing at camera
#             is_pointing_forward = vec_norm[2] < -0.5
            
#             # Update our checks
#             if not is_extended:
#                 all_fingers_extended = False
#             if not is_pointing_forward:
#                 all_fingers_pointing_forward = False
        
#         # Final posture validation
#         valid_posture = all_fingers_extended and all_fingers_pointing_forward
        
#         # Set debug reason
#         if not valid_posture:
#             if not all_fingers_extended:
#                 self.debug_info["last_validation_reason"] = "Not all fingers extended"
#             elif not all_fingers_pointing_forward:
#                 self.debug_info["last_validation_reason"] = "Fingers not pointing toward camera"
#         else:
#             self.debug_info["last_validation_reason"] = "Valid posture"
        
#         self.debug_info["posture_valid"] = valid_posture
#         return valid_posture
            
#     def detect_motion_gesture(self, landmarks, threshold: float = 0.1, 
#                              confidence_threshold: float = 0.6, 
#                              current_time: Optional[float] = None) -> Tuple[str, bool]:
#         """
#         Detect and validate motion gestures based on hand movement and posture.
        
#         Args:
#             landmarks: MediaPipe hand landmarks for posture validation
#             threshold: Minimum velocity magnitude to consider a swipe
#             confidence_threshold: Minimum ratio of dominant direction
#             current_time: Current timestamp (if None, uses time.time())
            
#         Returns:
#             Tuple of (gesture_type, is_validated):
#               - gesture_type: 'swipe_left', 'swipe_right', 'swipe_up', 'swipe_down', 'stationary'
#               - is_validated: Boolean indicating if it passed validation
#         """
#         if current_time is None:
#             current_time = time.time()
            
#         # First check posture validity
#         posture_valid = self.is_valid_hand_posture(landmarks)
        
#         # If posture is invalid, we don't need to check motion
#         if not posture_valid:
#             self.current_motion_candidate = None
#             self.motion_start_time = 0
#             return 'invalid_posture', False
            
#         # Detect the current motion direction
#         velocities = self.calculate_velocity(hand_idx=0, landmark_idx=8)
#         if not velocities or len(velocities) < 3:
#             return 'insufficient_data', False
        
#         # Calculate direction
#         recent_velocities = velocities[-3:]
#         avg_vx = sum(v['vx'] for v in recent_velocities) / len(recent_velocities)
#         avg_vy = sum(v['vy'] for v in recent_velocities) / len(recent_velocities)
        
#         avg_magnitude = math.sqrt(avg_vx**2 + avg_vy**2)
        
#         # Determine the motion direction
#         if avg_magnitude < threshold:
#             current_motion = 'stationary'
#         else:
#             x_confidence = abs(avg_vx) / avg_magnitude if avg_magnitude > 0 else 0
#             y_confidence = abs(avg_vy) / avg_magnitude if avg_magnitude > 0 else 0
            
#             if x_confidence > y_confidence and x_confidence > confidence_threshold:
#                 current_motion = 'swipe_right' if avg_vx > 0 else 'swipe_left'
#             elif y_confidence > x_confidence and y_confidence > confidence_threshold:
#                 current_motion = 'swipe_down' if avg_vy > 0 else 'swipe_up'
#             else:
#                 current_motion = 'stationary'
        
#         # Handle duration validation
#         if current_motion == 'stationary':
#             # Reset tracking when motion stops
#             self.current_motion_candidate = None
#             self.motion_start_time = 0
#             self.debug_info["tracking_duration"] = 0
#             return current_motion, False
            
#         # If this is a new motion, start tracking it
#         if current_motion != self.current_motion_candidate:
#             self.current_motion_candidate = current_motion
#             self.motion_start_time = current_time
#             self.debug_info["tracking_duration"] = 0
#             return current_motion, False
            
#         # Calculate how long this motion has been maintained
#         motion_duration = current_time - self.motion_start_time
#         self.debug_info["tracking_duration"] = motion_duration
        
#         # If the motion has been maintained long enough, validate it
#         if motion_duration >= self.min_gesture_duration:
#             self.validated_motion = current_motion
#             return current_motion, True
            
#         # Motion not yet valid based on duration
#         return current_motion, False
    
#     def reset_tracking(self) -> None:
#         """Reset the gesture tracking state."""
#         self.current_motion_candidate = None
#         self.motion_start_time = 0
#         self.validated_motion = None
        
#     def get_debug_info(self) -> Dict[str, Any]:
#         """Get debug information about the current tracking state."""
#         return {
#             "current_candidate": self.current_motion_candidate,
#             "has_validated_motion": self.validated_motion is not None,
#             "validation_reason": self.debug_info["last_validation_reason"],
#             "tracking_duration": self.debug_info["tracking_duration"],
#             "posture_valid": self.debug_info["posture_valid"],
#         }
        
#     def _distance_3d(self, landmark1, landmark2) -> float:
#         """Calculate 3D distance between landmarks."""
#         return math.sqrt(
#             (landmark1.x - landmark2.x)**2 +
#             (landmark1.y - landmark2.y)**2 +
#             (landmark1.z - landmark2.z)**2
#         )

"""
gesture_tracking.py - Enhanced hand landmarks tracking and gesture detection module

This module provides advanced gesture tracking functionality including:
- Tracking hand landmarks across multiple frames
- Filtering idle and transitional hand states
- Detecting intentional motion patterns
- Validating gestures based on duration, posture, and deliberate movement
"""

import math
import time
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from enum import Enum

class HandState(Enum):
    """Enumeration of possible hand movement states"""
    UNKNOWN = 0
    IDLE = 1        # Hand is present but not moving significantly
    TRANSITIONING = 2  # Hand is making small adjustments or transitioning
    DELIBERATE = 3  # Hand is making deliberate, intentional motion

class HandLandmarkTracker:
    """
    Tracks hand landmarks across frames to detect gestures with advanced filtering
    for improved reliability.
    """
    
    def __init__(self, 
                buffer_size: int = 10, 
                min_gesture_duration_ms: int = 500,
                motion_consistency_frames: int = 4,
                idle_velocity_threshold: float = 0.05,
                deliberate_velocity_threshold: float = 0.15,
                transition_window_ms: int = 300):
        """
        Initialize the hand landmark tracker with enhanced filtering.
        
        Args:
            buffer_size: Number of frames to keep in history for each landmark
            min_gesture_duration_ms: Minimum duration for gesture validation in milliseconds
            motion_consistency_frames: Number of frames to check for consistent motion
            idle_velocity_threshold: Maximum velocity magnitude for idle state
            deliberate_velocity_threshold: Minimum velocity for deliberate motion
            transition_window_ms: Time window to detect transitional states in milliseconds
        """
        self.logger = logging.getLogger(__name__)
        self.buffer_size = buffer_size
        self.min_gesture_duration = min_gesture_duration_ms / 1000.0  # Convert to seconds
        
        # Enhanced filtering parameters
        self.motion_consistency_frames = motion_consistency_frames
        self.idle_threshold = idle_velocity_threshold
        self.deliberate_threshold = deliberate_velocity_threshold
        self.transition_window = transition_window_ms / 1000.0  # Convert to seconds
        
        # Track landmarks history for velocity calculation
        self.landmark_history = {}  # {hand_id: {landmark_id: deque(positions)}}
        
        # Gesture state tracking
        self.current_motion_candidate = None
        self.motion_start_time = 0
        self.validated_motion = None
        self.current_hand_state = HandState.UNKNOWN
        
        # Motion consistency tracking
        self.recent_states = deque(maxlen=self.motion_consistency_frames)
        self.recent_directions = deque(maxlen=self.motion_consistency_frames)
        
        # Debug information
        self.debug_info = {
            "last_validation_reason": None,
            "tracking_duration": 0,
            "posture_valid": False,
            "hand_state": "UNKNOWN",
            "motion_consistency": 0.0,
            "avg_velocity": 0.0
        }
    
    def add_landmarks(self, multi_hand_landmarks: Any) -> None:
        """
        Add new hand landmarks with current timestamp for motion tracking.
        
        Args:
            multi_hand_landmarks: MediaPipe hand landmarks results
        """
        current_time = time.time()
        
        for hand_idx, hand_landmarks in enumerate(multi_hand_landmarks):
            # Create unique key for each hand
            hand_key = f"hand_{hand_idx}"
            
            # Initialize if this hand hasn't been seen before
            if hand_key not in self.landmark_history:
                self.landmark_history[hand_key] = {}
            
            # Process each landmark in the hand
            for i, landmark in enumerate(hand_landmarks.landmark):
                landmark_key = f"landmark_{i}"
                
                # Initialize if this landmark hasn't been tracked before
                if landmark_key not in self.landmark_history[hand_key]:
                    self.landmark_history[hand_key][landmark_key] = deque(maxlen=self.buffer_size)
                
                # Store the landmark position with timestamp
                self.landmark_history[hand_key][landmark_key].append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'timestamp': current_time
                })
    
    def get_landmark_trajectory(self, hand_idx: int = 0, landmark_idx: int = 8) -> List[Tuple[Dict[str, float], float]]:
        """
        Get the trajectory of a specific landmark over time.
        Default is index fingertip (landmark_idx 8) of first hand.
        
        Args:
            hand_idx: Hand index (0 for first detected hand)
            landmark_idx: Landmark index to track
            
        Returns:
            List of (position, timestamp) tuples
        """
        hand_key = f"hand_{hand_idx}"
        landmark_key = f"landmark_{landmark_idx}"
        
        if (hand_key not in self.landmark_history or
            landmark_key not in self.landmark_history[hand_key]):
            return []
        
        history = self.landmark_history[hand_key][landmark_key]
        return [(point, point['timestamp']) for point in history]
    
    # def calculate_velocity(self, hand_idx: int = 0, landmark_idx: int = 8) -> Optional[List[Dict[str, float]]]:
    #     """
    #     Calculate velocity of a landmark between frames.
        
    #     Args:
    #         hand_idx: Which hand to track (0 for first hand)
    #         landmark_idx: Which landmark to track (8 for index fingertip)
            
    #     Returns:
    #         List of velocity data dictionaries or None if not enough data
    #     """
    #     trajectory = self.get_landmark_trajectory(hand_idx, landmark_idx)
        
    #     if len(trajectory) < 2:
    #         return None
        
    #     velocities = []
    #     for i in range(1, len(trajectory)):
    #         curr_point, curr_time = trajectory[i]
    #         prev_point, prev_time = trajectory[i-1]
            
    #         # Calculate time difference
    #         dt = curr_time - prev_time
    #         if dt <= 0:
    #             continue
                
    #         # Calculate distance moved
    #         dx = curr_point['x'] - prev_point['x']
    #         dy = curr_point['y'] - prev_point['y']
    #         dz = curr_point['z'] - prev_point['z']
            
    #         # Calculate velocity components
    #         vx = dx / dt
    #         vy = dy / dt
    #         vz = dz / dt
            
    #         # Calculate velocity magnitude
    #         v_mag = math.sqrt(vx*vx + vy*vy + vz*vz)
            
    #         velocities.append({
    #             'timestamp': curr_time,
    #             'vx': vx, 
    #             'vy': vy, 
    #             'vz': vz,
    #             'magnitude': v_mag
    #         })
            
    #     return velocities
    
    def calculate_velocity(self, hand_idx: int = 0, landmark_idx: int = 8) -> Optional[List[Dict[str, float]]]:
        """
        Calculate velocity of a landmark between frames.
        
        Args:
            hand_idx: Which hand to track (0 for first hand)
            landmark_idx: Which landmark to track (8 for index fingertip)
            
        Returns:
            List of velocity data dictionaries or None if not enough data
        """
        trajectory = self.get_landmark_trajectory(hand_idx, landmark_idx)
        
        if len(trajectory) < 2:
            return None
        
        velocities = []
        
        # Process all pairs of consecutive points
        for i in range(1, len(trajectory)):
            curr_point, curr_time = trajectory[i]
            prev_point, prev_time = trajectory[i-1]
            
            # Calculate time difference
            dt = curr_time - prev_time
            if dt <= 0:
                self.logger.warning(f"Invalid time difference: {dt}. Skipping velocity calculation.")
                continue
                
            # Calculate distance moved
            dx = curr_point['x'] - prev_point['x']
            dy = curr_point['y'] - prev_point['y']
            dz = curr_point['z'] - prev_point['z']
            
            # Calculate velocity components
            vx = dx / dt
            vy = dy / dt
            vz = dz / dt
            
            # Calculate velocity magnitude
            v_mag = math.sqrt(vx*vx + vy*vy + vz*vz)
            
            velocities.append({
                'timestamp': curr_time,
                'vx': vx, 
                'vy': vy, 
                'vz': vz,
                'magnitude': v_mag
            })
        
        # Ensure we have the expected number of velocity calculations
        if len(velocities) != len(trajectory) - 1:
            self.logger.warning(f"Expected {len(trajectory) - 1} velocity samples, got {len(velocities)}")
            
        return velocities
    # def determine_hand_state(self, velocities: List[Dict[str, float]]) -> Tuple[HandState, float]:
    #     """
    #     Determine if the hand is in IDLE, TRANSITIONING, or DELIBERATE motion state
    #     based on velocity profile over multiple frames.
        
    #     Args:
    #         velocities: List of velocity measurements
            
    #     Returns:
    #         Tuple of (HandState, average_velocity_magnitude)
    #     """
    #     if not velocities or len(velocities) < 3:
    #         return HandState.UNKNOWN, 0.0
            
    #     # Calculate average velocity magnitude over recent frames
    #     recent_velocities = velocities[-min(len(velocities), self.motion_consistency_frames):]
    #     magnitudes = [v['magnitude'] for v in recent_velocities]
    #     avg_magnitude = sum(magnitudes) / len(magnitudes)
        
    #     # Calculate velocity variance as a measure of consistency
    #     variance = sum((m - avg_magnitude) ** 2 for m in magnitudes) / len(magnitudes)
    #     consistency = 1.0 / (1.0 + variance) if variance > 0 else 1.0
        
    #     # Analyze direction consistency
    #     directions = []
    #     for vel in recent_velocities:
    #         if vel['magnitude'] > self.idle_threshold:
    #             # Calculate normalized direction vector
    #             direction = (vel['vx'], vel['vy'], vel['vz'])
    #             magnitude = vel['magnitude']
    #             normalized = tuple(d/magnitude for d in direction)
    #             directions.append(normalized)
        
    #     direction_consistency = 0.0
    #     if len(directions) >= 2:
    #         # Calculate average dot product between consecutive direction vectors
    #         dot_products = []
    #         for i in range(1, len(directions)):
    #             dot = sum(a*b for a, b in zip(directions[i-1], directions[i]))
    #             dot_products.append(max(-1.0, min(1.0, dot)))  # Clamp to [-1,1]
            
    #         direction_consistency = sum(dot_products) / len(dot_products)
    #         # Convert from [-1,1] to [0,1] range
    #         direction_consistency = (direction_consistency + 1) / 2
        
    #     # Store for debugging
    #     self.debug_info["motion_consistency"] = consistency
    #     self.debug_info["direction_consistency"] = direction_consistency
    #     self.debug_info["avg_velocity"] = avg_magnitude
        
    #     # Determine state based on velocity profile and consistency
    #     if avg_magnitude < self.idle_threshold:
    #         return HandState.IDLE, avg_magnitude
    #     elif avg_magnitude > self.deliberate_threshold and consistency > 0.7:
    #         if direction_consistency > 0.85:  # High direction consistency
    #             return HandState.DELIBERATE, avg_magnitude
    #         else:
    #             return HandState.TRANSITIONING, avg_magnitude
    #     else:
    #         return HandState.TRANSITIONING, avg_magnitude
    
    def determine_hand_state(self, velocities: List[Dict[str, float]]) -> Tuple[HandState, float]:
        """
        Determine if the hand is in IDLE, TRANSITIONING, or DELIBERATE motion state
        based on velocity profile over multiple frames.
        
        Args:
            velocities: List of velocity measurements
            
        Returns:
            Tuple of (HandState, average_velocity_magnitude)
        """
        if not velocities or len(velocities) < 3:
            return HandState.UNKNOWN, 0.0
            
        # Calculate average velocity magnitude over recent frames
        recent_velocities = velocities[-min(len(velocities), self.motion_consistency_frames):]
        magnitudes = [v['magnitude'] for v in recent_velocities]
        avg_magnitude = sum(magnitudes) / len(magnitudes)
        
        # Calculate velocity variance as a measure of consistency
        variance = sum((m - avg_magnitude) ** 2 for m in magnitudes) / len(magnitudes)
        consistency = 1.0 / (1.0 + variance) if variance > 0 else 1.0
        
        # Analyze direction consistency
        directions = []
        for vel in recent_velocities:
            if vel['magnitude'] > self.idle_threshold:
                # Calculate normalized direction vector
                direction = (vel['vx'], vel['vy'], vel['vz'])
                magnitude = vel['magnitude']
                normalized = tuple(d/magnitude for d in direction)
                directions.append(normalized)
        
        direction_consistency = 0.0
        if len(directions) >= 2:
            # Calculate average dot product between consecutive direction vectors
            dot_products = []
            for i in range(1, len(directions)):
                dot = sum(a*b for a, b in zip(directions[i-1], directions[i]))
                dot_products.append(max(-1.0, min(1.0, dot)))  # Clamp to [-1,1]
            
            direction_consistency = sum(dot_products) / len(dot_products)
            # Convert from [-1,1] to [0,1] range
            direction_consistency = (direction_consistency + 1) / 2
        
        # Store for debugging
        self.debug_info["motion_consistency"] = consistency
        self.debug_info["direction_consistency"] = direction_consistency
        self.debug_info["avg_velocity"] = avg_magnitude
        
        # More strict criteria for DELIBERATE state
        if avg_magnitude < self.idle_threshold:
            return HandState.IDLE, avg_magnitude
        elif (avg_magnitude > self.deliberate_threshold and 
            consistency > 0.8 and  # Increased from 0.7
            direction_consistency > 0.9):  # Increased from 0.85
            return HandState.DELIBERATE, avg_magnitude
        else:
            return HandState.TRANSITIONING, avg_magnitude

    # def is_motion_consistent(self, current_motion: str) -> bool:
    #     """
    #     Check if the current motion direction is consistent over multiple frames.
        
    #     Args:
    #         current_motion: The current detected motion
            
    #     Returns:
    #         True if motion is consistent, False otherwise
    #     """
    #     # Skip consistency check for non-directional motions
    #     if current_motion in ['stationary', 'insufficient_data', 'invalid_posture']:
    #         return False
            
    #     # Add current direction to history
    #     self.recent_directions.append(current_motion)
        
    #     # Need enough history for consistency check
    #     if len(self.recent_directions) < self.motion_consistency_frames // 2:
    #         return False
            
    #     # Count occurrences of each direction
    #     direction_counts = {}
    #     for direction in self.recent_directions:
    #         direction_counts[direction] = direction_counts.get(direction, 0) + 1
            
    #     # Check if the current motion is the most frequent and appears enough times
    #     if current_motion in direction_counts:
    #         max_count = max(direction_counts.values())
    #         consistency_ratio = direction_counts[current_motion] / len(self.recent_directions)
    #         return (direction_counts[current_motion] == max_count and 
    #                 consistency_ratio > 0.6)  # At least 60% consistent
        
    #     return False
    
    def is_motion_consistent(self, current_motion: str) -> bool:
        """
        Check if the current motion direction is consistent over multiple frames.
        
        Args:
            current_motion: The current detected motion
            
        Returns:
            True if motion is consistent, False otherwise
        """
        # Skip consistency check for non-directional motions
        if current_motion in ['stationary', 'insufficient_data', 'invalid_posture', 'transitioning', 'unclear_direction']:
            return False
            
        # Add current direction to history
        self.recent_directions.append(current_motion)
        
        # Need enough history for consistency check - at least half of required frames
        min_required = max(2, self.motion_consistency_frames // 2)
        if len(self.recent_directions) < min_required:
            self.logger.debug(f"Not enough direction history: {len(self.recent_directions)}/{min_required}")
            return False
            
        # Count occurrences of each direction
        direction_counts = {}
        for direction in self.recent_directions:
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
            
        # Check if the current motion is the most frequent and appears enough times
        if current_motion in direction_counts:
            max_count = max(direction_counts.values())
            total_directions = len(self.recent_directions)
            consistency_ratio = direction_counts[current_motion] / total_directions
            
            is_most_frequent = direction_counts[current_motion] == max_count
            is_frequent_enough = consistency_ratio > 0.65  # Requires at least 65% consistency
            
            self.logger.debug(
                f"Motion consistency: {current_motion}, ratio: {consistency_ratio:.2f}, "
                f"most frequent: {is_most_frequent}, frequent enough: {is_frequent_enough}"
            )
            
            return is_most_frequent and is_frequent_enough and total_directions >= min_required
        
        return False
    def is_valid_hand_posture(self, landmarks) -> bool:
        """
        Check if hand posture is valid: all fingers (except thumb) fully extended 
        and pointing toward camera.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            True if posture is valid, False otherwise
        """
        # Exit early if no landmarks
        if not landmarks:
            self.debug_info["last_validation_reason"] = "No landmarks"
            return False
        
        # Finger joints - PIP is Proximal Interphalangeal Joint (middle joint)
        # DIP is Distal Interphalangeal Joint (joint nearest to fingertip)
        finger_joints = {
            'index': {'mcp': 5, 'pip': 6, 'dip': 7, 'tip': 8},
            'middle': {'mcp': 9, 'pip': 10, 'dip': 11, 'tip': 12},
            'ring': {'mcp': 13, 'pip': 14, 'dip': 15, 'tip': 16},
            'pinky': {'mcp': 17, 'pip': 18, 'dip': 19, 'tip': 20}
        }
        
        # Check each finger (excluding thumb)
        all_fingers_extended = True
        all_fingers_pointing_forward = True
        
        # Calculate palm normal to check finger orientation relative to palm
        wrist = landmarks[0]
        index_mcp = landmarks[5]
        pinky_mcp = landmarks[17]
        
        # Vectors to define palm plane
        v1 = (index_mcp.x - wrist.x, index_mcp.y - wrist.y, index_mcp.z - wrist.z)
        v2 = (pinky_mcp.x - wrist.x, pinky_mcp.y - wrist.y, pinky_mcp.z - wrist.z)
        
        # Cross product to get palm normal
        palm_normal = (
            v1[1]*v2[2] - v1[2]*v2[1],
            v1[2]*v2[0] - v1[0]*v2[2],
            v1[0]*v2[1] - v1[1]*v2[0]
        )
        
        # Normalize palm normal
        normal_magnitude = math.sqrt(sum(x*x for x in palm_normal))
        if normal_magnitude > 0:
            palm_normal = tuple(x/normal_magnitude for x in palm_normal)
        
        for finger_name, joints in finger_joints.items():
            # 1. Check if finger is extended by comparing tip to base distance
            mcp = landmarks[joints['mcp']]
            pip = landmarks[joints['pip']]
            dip = landmarks[joints['dip']]
            tip = landmarks[joints['tip']]
            
            # Calculate finger segment lengths
            mcp_to_pip_length = self._distance_3d(mcp, pip)
            pip_to_dip_length = self._distance_3d(pip, dip)
            dip_to_tip_length = self._distance_3d(dip, tip)
            
            # Calculate direct distance from MCP to tip
            direct_distance = self._distance_3d(mcp, tip)
            
            # Sum of finger segment lengths
            total_finger_length = mcp_to_pip_length + pip_to_dip_length + dip_to_tip_length
            
            # Finger is considered extended if direct distance is at least 75% of total length
            extension_ratio = direct_distance / total_finger_length if total_finger_length > 0 else 0
            is_extended = extension_ratio > 0.75
            
            # 2. Check if finger is pointing away from palm (using dot product with palm normal)
            # Calculate finger direction vector (from MCP to tip)
            finger_direction = (tip.x - mcp.x, tip.y - mcp.y, tip.z - mcp.z)
            
            # Normalize finger direction
            dir_magnitude = math.sqrt(sum(x*x for x in finger_direction))
            if dir_magnitude > 0:
                finger_direction = tuple(x/dir_magnitude for x in finger_direction)
                
            # Dot product with palm normal - negative means pointing in opposite direction of palm normal
            # In MediaPipe coordinate system, fingers pointing toward camera have negative z
            dot_with_normal = sum(a*b for a, b in zip(finger_direction, palm_normal))
            
            # Check z component - should be significant
            is_pointing_forward = finger_direction[2] < -0.6 and dot_with_normal < 0
            
            # Update our checks
            if not is_extended:
                all_fingers_extended = False
            if not is_pointing_forward:
                all_fingers_pointing_forward = False
        
        # Final posture validation
        valid_posture = all_fingers_extended and all_fingers_pointing_forward
        
        # Set debug reason
        if not valid_posture:
            if not all_fingers_extended:
                self.debug_info["last_validation_reason"] = "Not all fingers extended"
            elif not all_fingers_pointing_forward:
                self.debug_info["last_validation_reason"] = "Fingers not pointing toward camera"
        else:
            self.debug_info["last_validation_reason"] = "Valid posture"
        
        self.debug_info["posture_valid"] = valid_posture
        return valid_posture
            
    # def detect_motion_gesture(self, landmarks, threshold: float = 0.1, 
    #                          confidence_threshold: float = 0.6, 
    #                          current_time: Optional[float] = None) -> Tuple[str, bool]:
    #     """
    #     Detect and validate motion gestures with enhanced filtering to distinguish
    #     deliberate gestures from transitional or idle movements.
        
    #     Args:
    #         landmarks: MediaPipe hand landmarks for posture validation
    #         threshold: Minimum velocity magnitude to consider a swipe
    #         confidence_threshold: Minimum ratio of dominant direction
    #         current_time: Current timestamp (if None, uses time.time())
            
    #     Returns:
    #         Tuple of (gesture_type, is_validated):
    #           - gesture_type: 'swipe_left', 'swipe_right', 'swipe_up', 'swipe_down', 'stationary'
    #           - is_validated: Boolean indicating if it passed validation
    #     """
    #     if current_time is None:
    #         current_time = time.time()
            
    #     # First check posture validity
    #     posture_valid = self.is_valid_hand_posture(landmarks)
        
    #     # If posture is invalid, we don't need to check motion
    #     if not posture_valid:
    #         self.current_motion_candidate = None
    #         self.motion_start_time = 0
    #         return 'invalid_posture', False
            
    #     # Detect the current motion direction
    #     velocities = self.calculate_velocity(hand_idx=0, landmark_idx=8)
    #     if not velocities or len(velocities) < 3:
    #         self.current_hand_state = HandState.UNKNOWN
    #         self.debug_info["hand_state"] = "UNKNOWN"
    #         return 'insufficient_data', False
        
    #     # Determine hand movement state
    #     hand_state, avg_magnitude = self.determine_hand_state(velocities)
    #     self.current_hand_state = hand_state
    #     self.debug_info["hand_state"] = hand_state.name
        
    #     # Add current state to history
    #     self.recent_states.append(hand_state)
        
    #     # Calculate direction from velocities
    #     recent_velocities = velocities[-min(3, len(velocities)):]
    #     avg_vx = sum(v['vx'] for v in recent_velocities) / len(recent_velocities)
    #     avg_vy = sum(v['vy'] for v in recent_velocities) / len(recent_velocities)
        
    #     # Only process deliberate movements
    #     if hand_state != HandState.DELIBERATE:
    #         # Reset motion tracking for non-deliberate states
    #         if hand_state == HandState.IDLE:
    #             self.current_motion_candidate = None
    #             self.motion_start_time = 0
                
    #         # If we're in a transitional state, we may be preparing for a real gesture
    #         # but we don't validate it yet
    #         return 'stationary' if hand_state == HandState.IDLE else 'transitioning', False
        
    #     # For deliberate movements, determine the direction
    #     # Calculate magnitude of the average velocity vector
    #     avg_magnitude = math.sqrt(avg_vx**2 + avg_vy**2)
        
    #     # Skip if magnitude is too small (not enough movement)
    #     if avg_magnitude < threshold:
    #         return 'stationary', False
            
    #     # Calculate directional confidence
    #     x_confidence = abs(avg_vx) / avg_magnitude if avg_magnitude > 0 else 0
    #     y_confidence = abs(avg_vy) / avg_magnitude if avg_magnitude > 0 else 0
        
    #     # Determine the motion direction based on highest confidence
    #     if x_confidence > y_confidence and x_confidence > confidence_threshold:
    #         # Primarily horizontal motion
    #         current_motion = 'swipe_right' if avg_vx > 0 else 'swipe_left'
    #     elif y_confidence > x_confidence and y_confidence > confidence_threshold:
    #         # Primarily vertical motion
    #         current_motion = 'swipe_down' if avg_vy > 0 else 'swipe_up'
    #     else:
    #         # Motion is not clearly in any cardinal direction
    #         current_motion = 'unclear_direction'
            
    #     # Check motion consistency over time
    #     is_consistent = self.is_motion_consistent(current_motion)
        
    #     # If motion is unclear or not consistent, don't validate
    #     if current_motion == 'unclear_direction' or not is_consistent:
    #         return current_motion, False
            
    #     # Handle duration validation for consistent, deliberate motion
    #     # If this is a new motion, start tracking it
    #     if current_motion != self.current_motion_candidate:
    #         self.current_motion_candidate = current_motion
    #         self.motion_start_time = current_time
    #         self.debug_info["tracking_duration"] = 0
    #         return current_motion, False
            
    #     # Calculate how long this motion has been maintained
    #     motion_duration = current_time - self.motion_start_time
    #     self.debug_info["tracking_duration"] = motion_duration
        
    #     # If the motion has been maintained long enough, validate it
    #     if motion_duration >= self.min_gesture_duration:
    #         self.validated_motion = current_motion
    #         return current_motion, True
            
    #     # Motion not yet valid based on duration
    #     return current_motion, False
    
    def detect_motion_gesture(self, landmarks, threshold: float = 0.1, 
                         confidence_threshold: float = 0.6, 
                         current_time: Optional[float] = None) -> Tuple[str, bool]:
        """
        Detect and validate motion gestures with enhanced filtering to distinguish
        deliberate gestures from transitional or idle movements.
        
        Args:
            landmarks: MediaPipe hand landmarks for posture validation
            threshold: Minimum velocity magnitude to consider a swipe
            confidence_threshold: Minimum ratio of dominant direction
            current_time: Current timestamp (if None, uses time.time())
            
        Returns:
            Tuple of (gesture_type, is_validated):
            - gesture_type: 'swipe_left', 'swipe_right', 'swipe_up', 'swipe_down', 'stationary'
            - is_validated: Boolean indicating if it passed validation
        """
        if current_time is None:
            current_time = time.time()
            
        # First check posture validity
        posture_valid = self.is_valid_hand_posture(landmarks)
        
        # If posture is invalid, we don't need to check motion
        if not posture_valid:
            self.current_motion_candidate = None
            self.motion_start_time = 0
            return 'invalid_posture', False
            
        # Detect the current motion direction
        velocities = self.calculate_velocity(hand_idx=0, landmark_idx=8)
        if not velocities or len(velocities) < 3:
            self.current_hand_state = HandState.UNKNOWN
            self.debug_info["hand_state"] = "UNKNOWN"
            return 'insufficient_data', False
        
        # Determine hand movement state
        hand_state, avg_magnitude = self.determine_hand_state(velocities)
        self.current_hand_state = hand_state
        self.debug_info["hand_state"] = hand_state.name
        
        # Add current state to history
        self.recent_states.append(hand_state)
        
        # Calculate direction from velocities
        recent_velocities = velocities[-min(3, len(velocities)):]
        avg_vx = sum(v['vx'] for v in recent_velocities) / len(recent_velocities)
        avg_vy = sum(v['vy'] for v in recent_velocities) / len(recent_velocities)
        
        # Only process deliberate movements
        if hand_state != HandState.DELIBERATE:
            # Reset motion tracking for non-deliberate states
            if hand_state == HandState.IDLE:
                self.current_motion_candidate = None
                self.motion_start_time = 0
                
            # If we're in a transitional state, we may be preparing for a real gesture
            # but we don't validate it yet
            return 'stationary' if hand_state == HandState.IDLE else 'transitioning', False
        
        # For deliberate movements, determine the direction
        # Calculate magnitude of the average velocity vector
        avg_magnitude = math.sqrt(avg_vx**2 + avg_vy**2)
        
        # Skip if magnitude is too small (not enough movement)
        if avg_magnitude < threshold:
            return 'stationary', False
            
        # Calculate directional confidence
        x_confidence = abs(avg_vx) / avg_magnitude if avg_magnitude > 0 else 0
        y_confidence = abs(avg_vy) / avg_magnitude if avg_magnitude > 0 else 0
        
        # Determine the motion direction based on highest confidence
        if x_confidence > y_confidence and x_confidence > confidence_threshold:
            # Primarily horizontal motion
            current_motion = 'swipe_right' if avg_vx > 0 else 'swipe_left'
        elif y_confidence > x_confidence and y_confidence > confidence_threshold:
            # Primarily vertical motion
            current_motion = 'swipe_down' if avg_vy > 0 else 'swipe_up'
        else:
            # Motion is not clearly in any cardinal direction
            current_motion = 'unclear_direction'
            
        # Check motion consistency over time
        is_consistent = self.is_motion_consistent(current_motion)
        
        # If motion is unclear or not consistent, don't validate
        if current_motion == 'unclear_direction' or not is_consistent:
            return current_motion, False
            
        # Handle duration validation for consistent, deliberate motion
        # If this is a new motion, start tracking it
        if current_motion != self.current_motion_candidate:
            self.current_motion_candidate = current_motion
            self.motion_start_time = current_time
            self.debug_info["tracking_duration"] = 0
            return current_motion, False
            
        # Calculate how long this motion has been maintained
        motion_duration = current_time - self.motion_start_time
        self.debug_info["tracking_duration"] = motion_duration
        
        # Verify hand state has been DELIBERATE for long enough
        deliberate_count = sum(1 for s in self.recent_states if s == HandState.DELIBERATE)
        deliberate_ratio = deliberate_count / len(self.recent_states) if self.recent_states else 0
        
        # If the motion has been maintained long enough and hand state has been consistently DELIBERATE
        if motion_duration >= self.min_gesture_duration and deliberate_ratio >= 0.75:
            self.validated_motion = current_motion
            return current_motion, True
            
        # Motion not yet valid based on duration or state consistency
        return current_motion, False

    def reset_tracking(self) -> None:
        """Reset the gesture tracking state."""
        self.current_motion_candidate = None
        self.motion_start_time = 0
        self.validated_motion = None
        self.recent_states.clear()
        self.recent_directions.clear()
        
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the current tracking state."""
        return {
            "current_candidate": self.current_motion_candidate,
            "has_validated_motion": self.validated_motion is not None,
            "validation_reason": self.debug_info["last_validation_reason"],
            "tracking_duration": self.debug_info["tracking_duration"],
            "posture_valid": self.debug_info["posture_valid"],
            "hand_state": self.debug_info["hand_state"],
            "motion_consistency": self.debug_info.get("motion_consistency", 0),
            "direction_consistency": self.debug_info.get("direction_consistency", 0),
            "avg_velocity": self.debug_info.get("avg_velocity", 0),
        }
        
    def _distance_3d(self, landmark1, landmark2) -> float:
        """Calculate 3D distance between landmarks."""
        return math.sqrt(
            (landmark1.x - landmark2.x)**2 +
            (landmark1.y - landmark2.y)**2 +
            (landmark1.z - landmark2.z)**2
        )