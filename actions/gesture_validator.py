import time
import math
import numpy as np
from typing import Dict, List, Optional, Tuple

class GestureValidator:
    """
    Validates gestures based on duration and hand posture criteria to ensure 
    reliable gesture detection and prevent accidental triggers.
    """
    
    def __init__(self, min_gesture_duration_ms: int = 500):
        """
        Initialize the gesture validator.
        
        Args:
            min_gesture_duration_ms: Minimum duration in milliseconds for a gesture to be considered valid
        """
        self.min_gesture_duration = min_gesture_duration_ms / 1000.0  # Convert to seconds
        
        # Gesture state tracking
        self.current_gesture_candidate = None
        self.gesture_start_time = 0
        self.validated_gesture = None
        
        # Posture tracking
        self.previous_posture_valid = False
        
        # Debug information
        self.last_validation_reason = None
    
    def is_valid_hand_posture(self, landmarks) -> bool:
        """
        Check if hand posture is valid: all fingers (except thumb) fully extended and pointing toward camera.
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            True if posture is valid, False otherwise
        """
        # Exit early if no landmarks
        if not landmarks:
            self.last_validation_reason = "No landmarks"
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
                self.last_validation_reason = "Not all fingers extended"
            elif not all_fingers_pointing_forward:
                self.last_validation_reason = "Fingers not pointing toward camera"
        else:
            self.last_validation_reason = "Valid posture"
            
        return valid_posture
    
    def validate_gesture(self, current_gesture: str, landmarks, current_time: float) -> Optional[str]:
        """
        Validate a gesture based on duration and hand posture.
        
        Args:
            current_gesture: The currently detected gesture
            landmarks: MediaPipe hand landmarks
            current_time: Current timestamp
            
        Returns:
            Validated gesture if valid, None otherwise
        """
        # Skip validation if gesture is None or 'unknown'
        if not current_gesture or current_gesture == 'unknown':
            self.current_gesture_candidate = None
            self.gesture_start_time = 0
            return None
        
        # First check posture validity
        posture_valid = self.is_valid_hand_posture(landmarks)
        
        # If posture became invalid, reset gesture candidate
        if not posture_valid and self.previous_posture_valid:
            self.current_gesture_candidate = None
            self.gesture_start_time = 0
            self.validated_gesture = None
            self.previous_posture_valid = False
            return None
        
        # Update posture validity state
        self.previous_posture_valid = posture_valid
        
        # If posture is not valid, no need to check duration
        if not posture_valid:
            return None
        
        # If this is a new candidate gesture, start tracking it
        if current_gesture != self.current_gesture_candidate:
            self.current_gesture_candidate = current_gesture
            self.gesture_start_time = current_time
            return None
        
        # Calculate how long this gesture has been maintained
        gesture_duration = current_time - self.gesture_start_time
        
        # If the gesture has been maintained long enough, validate it
        if gesture_duration >= self.min_gesture_duration:
            self.validated_gesture = current_gesture
            return current_gesture
        
        # Not yet valid based on duration
        return None
    
    def reset(self):
        """Reset the gesture validator state."""
        self.current_gesture_candidate = None
        self.gesture_start_time = 0
        self.validated_gesture = None
        self.previous_posture_valid = False
        
    def _distance_3d(self, landmark1, landmark2) -> float:
        """Calculate 3D distance between landmarks."""
        return math.sqrt(
            (landmark1.x - landmark2.x)**2 +
            (landmark1.y - landmark2.y)**2 +
            (landmark1.z - landmark2.z)**2
        )
    
    def get_debug_info(self) -> Dict:
        """Get debug information about the current validation state."""
        return {
            "current_candidate": self.current_gesture_candidate,
            "has_validated_gesture": self.validated_gesture is not None,
            "validation_reason": self.last_validation_reason,
            "tracking_duration": time.time() - self.gesture_start_time if self.gesture_start_time > 0 else 0
        }