"""
gesture_tracking.py - Hand landmarks tracking and gesture detection module

This module provides gesture tracking functionality including:
- Tracking hand landmarks across multiple frames
- Calculating motion trajectories and velocities
- Detecting directional gestures with validation
- Providing reliable gesture recognition with duration and posture validation
"""

import math
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
import numpy as np

class HandLandmarkTracker:
    """
    Tracks hand landmarks across frames to detect gestures and validate
    them based on duration and posture criteria.
    """
    
    def __init__(self, buffer_size: int = 10, min_gesture_duration_ms: int = 500):
        """
        Initialize the hand landmark tracker.
        
        Args:
            buffer_size: Number of frames to keep in history for each landmark
            min_gesture_duration_ms: Minimum duration for gesture validation in milliseconds
        """
        self.logger = logging.getLogger(__name__)
        self.buffer_size = buffer_size
        self.min_gesture_duration = min_gesture_duration_ms / 1000.0  # Convert to seconds
        
        # Track landmarks history for velocity calculation
        self.landmark_history = {}  # {hand_id: {landmark_id: deque(positions)}}
        
        # Gesture state tracking
        self.current_motion_candidate = None
        self.motion_start_time = 0
        self.validated_motion = None
        
        # Debug information
        self.debug_info = {
            "last_validation_reason": None,
            "tracking_duration": 0,
            "posture_valid": False
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
        for i in range(1, len(trajectory)):
            curr_point, curr_time = trajectory[i]
            prev_point, prev_time = trajectory[i-1]
            
            # Calculate time difference
            dt = curr_time - prev_time
            if dt <= 0:
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
            
        return velocities
    
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
            
            # 2. Check if finger is pointing toward camera (z-direction)
            # Calculate vectors along finger
            vec_mcp_to_tip = (tip.x - mcp.x, tip.y - mcp.y, tip.z - mcp.z)
            
            # Normalize the vector
            magnitude = math.sqrt(vec_mcp_to_tip[0]**2 + vec_mcp_to_tip[1]**2 + vec_mcp_to_tip[2]**2)
            if magnitude > 0:
                vec_norm = (vec_mcp_to_tip[0]/magnitude, vec_mcp_to_tip[1]/magnitude, vec_mcp_to_tip[2]/magnitude)
            else:
                vec_norm = (0, 0, 0)
            
            # Check z component - negative means pointing toward camera in MediaPipe coordinates
            # The z component should be significant (at least 0.5 in magnitude) when pointing at camera
            is_pointing_forward = vec_norm[2] < -0.5
            
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
            
    def detect_motion_gesture(self, landmarks, threshold: float = 0.1, 
                             confidence_threshold: float = 0.6, 
                             current_time: Optional[float] = None) -> Tuple[str, bool]:
        """
        Detect and validate motion gestures based on hand movement and posture.
        
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
            return 'insufficient_data', False
        
        # Calculate direction
        recent_velocities = velocities[-3:]
        avg_vx = sum(v['vx'] for v in recent_velocities) / len(recent_velocities)
        avg_vy = sum(v['vy'] for v in recent_velocities) / len(recent_velocities)
        
        avg_magnitude = math.sqrt(avg_vx**2 + avg_vy**2)
        
        # Determine the motion direction
        if avg_magnitude < threshold:
            current_motion = 'stationary'
        else:
            x_confidence = abs(avg_vx) / avg_magnitude if avg_magnitude > 0 else 0
            y_confidence = abs(avg_vy) / avg_magnitude if avg_magnitude > 0 else 0
            
            if x_confidence > y_confidence and x_confidence > confidence_threshold:
                current_motion = 'swipe_right' if avg_vx > 0 else 'swipe_left'
            elif y_confidence > x_confidence and y_confidence > confidence_threshold:
                current_motion = 'swipe_down' if avg_vy > 0 else 'swipe_up'
            else:
                current_motion = 'stationary'
        
        # Handle duration validation
        if current_motion == 'stationary':
            # Reset tracking when motion stops
            self.current_motion_candidate = None
            self.motion_start_time = 0
            self.debug_info["tracking_duration"] = 0
            return current_motion, False
            
        # If this is a new motion, start tracking it
        if current_motion != self.current_motion_candidate:
            self.current_motion_candidate = current_motion
            self.motion_start_time = current_time
            self.debug_info["tracking_duration"] = 0
            return current_motion, False
            
        # Calculate how long this motion has been maintained
        motion_duration = current_time - self.motion_start_time
        self.debug_info["tracking_duration"] = motion_duration
        
        # If the motion has been maintained long enough, validate it
        if motion_duration >= self.min_gesture_duration:
            self.validated_motion = current_motion
            return current_motion, True
            
        # Motion not yet valid based on duration
        return current_motion, False
    
    def reset_tracking(self) -> None:
        """Reset the gesture tracking state."""
        self.current_motion_candidate = None
        self.motion_start_time = 0
        self.validated_motion = None
        
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the current tracking state."""
        return {
            "current_candidate": self.current_motion_candidate,
            "has_validated_motion": self.validated_motion is not None,
            "validation_reason": self.debug_info["last_validation_reason"],
            "tracking_duration": self.debug_info["tracking_duration"],
            "posture_valid": self.debug_info["posture_valid"],
        }
        
    def _distance_3d(self, landmark1, landmark2) -> float:
        """Calculate 3D distance between landmarks."""
        return math.sqrt(
            (landmark1.x - landmark2.x)**2 +
            (landmark1.y - landmark2.y)**2 +
            (landmark1.z - landmark2.z)**2
        )