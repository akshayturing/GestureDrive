# utils/gesture_utils.py
import math
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import logging

class GestureUtils:
    """
    Utility class for gesture detection calculations.
    Consolidates shared gesture recognition logic.
    """
    
    @staticmethod
    def calculate_finger_angles(landmarks: List[Any]) -> Dict[str, float]:
        """
        Calculate angles between finger joints for more robust pose detection.
        
        Args:
            landmarks: List of hand landmarks from MediaPipe
            
        Returns:
            Dictionary of angles for each finger
        """
        # Point indices for each finger
        THUMB_POINTS = [0, 1, 2, 3, 4]
        INDEX_POINTS = [0, 5, 6, 7, 8]
        MIDDLE_POINTS = [0, 9, 10, 11, 12]
        RING_POINTS = [0, 13, 14, 15, 16]
        PINKY_POINTS = [0, 17, 18, 19, 20]
        
        # Calculate angles
        angles = {
            "thumb": GestureUtils._calculate_finger_angle(landmarks, THUMB_POINTS),
            "index": GestureUtils._calculate_finger_angle(landmarks, INDEX_POINTS),
            "middle": GestureUtils._calculate_finger_angle(landmarks, MIDDLE_POINTS),
            "ring": GestureUtils._calculate_finger_angle(landmarks, RING_POINTS),
            "pinky": GestureUtils._calculate_finger_angle(landmarks, PINKY_POINTS)
        }
        
        return angles
    
    @staticmethod
    def _calculate_finger_angle(landmarks: List[Any], points: List[int]) -> float:
        """
        Calculate the angle between finger joints
        
        Args:
            landmarks: List of landmarks
            points: List of point indices for the finger
            
        Returns:
            Angle in degrees
        """
        if len(points) < 3 or landmarks is None:
            return 0.0
        
        # Get the three points for angle calculation (MCP, PIP, DIP)
        mcp = np.array([landmarks[points[1]].x, landmarks[points[1]].y, landmarks[points[1]].z])
        pip = np.array([landmarks[points[2]].x, landmarks[points[2]].y, landmarks[points[2]].z])
        dip = np.array([landmarks[points[3]].x, landmarks[points[3]].y, landmarks[points[3]].z])
        
        # Calculate vectors
        v1 = mcp - pip
        v2 = dip - pip
        
        # Calculate angle using dot product
        cosine_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    @staticmethod
    def is_finger_extended(landmarks: List[Any], fingertip_id: int, 
                           mcp_id: int, extension_threshold: float = 0.1) -> bool:
        """
        Determine if a finger is extended based on fingertip distance from palm.
        
        Args:
            landmarks: List of landmarks
            fingertip_id: ID of fingertip landmark
            mcp_id: ID of metacarpophalangeal (base knuckle) landmark
            extension_threshold: Threshold for determining extension
            
        Returns:
            Boolean indicating if finger is extended
        """
        if landmarks is None:
            return False
            
        # Get wrist position as reference point
        wrist = landmarks[0]
        
        # Get fingertip and base positions
        fingertip = landmarks[fingertip_id]
        mcp = landmarks[mcp_id]
        
        # Calculate distances
        wrist_to_mcp = GestureUtils._distance_3d(wrist, mcp)
        wrist_to_tip = GestureUtils._distance_3d(wrist, fingertip)
        mcp_to_tip = GestureUtils._distance_3d(mcp, fingertip)
        
        # A finger is considered extended if the fingertip is farther 
        # from the wrist than the MCP joint
        extension_ratio = wrist_to_tip / wrist_to_mcp if wrist_to_mcp > 0 else 0
        
        # Also check straightness - distance from MCP to tip should be significant
        return extension_ratio > (1.0 + extension_threshold) and mcp_to_tip > 0.08
    
    @staticmethod
    def get_finger_extension_state(landmarks: List[Any]) -> Dict[str, bool]:
        """
        Get extension state for all fingers at once.
        
        Args:
            landmarks: List of landmarks
            
        Returns:
            Dictionary with extension state for each finger
        """
        if landmarks is None:
            return {
                "thumb": False,
                "index": False,
                "middle": False,
                "ring": False,
                "pinky": False
            }
            
        return {
            "thumb": GestureUtils._is_thumb_extended(landmarks),
            "index": GestureUtils.is_finger_extended(landmarks, 8, 5),  # Index finger
            "middle": GestureUtils.is_finger_extended(landmarks, 12, 9),  # Middle finger
            "ring": GestureUtils.is_finger_extended(landmarks, 16, 13),  # Ring finger
            "pinky": GestureUtils.is_finger_extended(landmarks, 20, 17)  # Pinky finger
        }
    
    @staticmethod
    def _is_thumb_extended(landmarks: List[Any]) -> bool:
        """
        Special case for thumb extension detection.
        
        Args:
            landmarks: List of landmarks
            
        Returns:
            Boolean indicating if thumb is extended
        """
        if landmarks is None:
            return False
            
        # Thumb has different geometry than other fingers
        wrist = landmarks[0]
        thumb_cmc = landmarks[1]  # Carpometacarpal joint  
        thumb_mcp = landmarks[2]  # Metacarpophalangeal joint
        thumb_ip = landmarks[3]   # Interphalangeal joint
        thumb_tip = landmarks[4]  # Fingertip
        
        # Calculate direction vectors
        cmc_to_mcp = np.array([thumb_mcp.x - thumb_cmc.x, 
                                thumb_mcp.y - thumb_cmc.y,
                                thumb_mcp.z - thumb_cmc.z])
        
        mcp_to_ip = np.array([thumb_ip.x - thumb_mcp.x,
                              thumb_ip.y - thumb_mcp.y,
                              thumb_ip.z - thumb_mcp.z])
        
        ip_to_tip = np.array([thumb_tip.x - thumb_ip.x,
                              thumb_tip.y - thumb_ip.y,
                              thumb_tip.z - thumb_ip.z])
        
        # Normalize vectors
        if np.linalg.norm(cmc_to_mcp) > 0 and np.linalg.norm(mcp_to_ip) > 0:
            cmc_to_mcp = cmc_to_mcp / np.linalg.norm(cmc_to_mcp)
            mcp_to_ip = mcp_to_ip / np.linalg.norm(mcp_to_ip)
            
            # Calculate dot product - negative means thumb is folded inward
            dot_product = np.dot(cmc_to_mcp, mcp_to_ip)
            
            # Also check if tip is far from wrist
            wrist_to_tip = GestureUtils._distance_3d(wrist, thumb_tip)
            wrist_to_mcp = GestureUtils._distance_3d(wrist, thumb_mcp)
            
            distance_ratio = wrist_to_tip / wrist_to_mcp if wrist_to_mcp > 0 else 0
            
            # Combine both checks for robust detection
            return dot_product > 0.1 and distance_ratio > 1.5
        
        return False
    
    @staticmethod
    def get_pointing_direction(landmarks: List[Any]) -> str:
        """
        Determine pointing direction based on index finger.
        
        Args:
            landmarks: List of landmarks
            
        Returns:
            Direction string: "point_up", "point_down", "point_left", "point_right"
        """
        if landmarks is None:
            return "unknown"
            
        # Get relevant points
        index_mcp = landmarks[5]  # Index base
        index_tip = landmarks[8]  # Index tip
        
        # Calculate vector from MCP to tip
        dx = index_tip.x - index_mcp.x
        dy = index_tip.y - index_mcp.y
        
        # Determine primary direction
        if abs(dx) > abs(dy):
            # Horizontal pointing
            return "point_right" if dx > 0 else "point_left"
        else:
            # Vertical pointing
            return "point_up" if dy < 0 else "point_down"
    
    @staticmethod
    def calculate_hand_orientation(landmarks: List[Any]) -> float:
        """
        Calculate hand orientation angle.
        
        Args:
            landmarks: List of landmarks
            
        Returns:
            Orientation angle in degrees (0-360)
        """
        if landmarks is None:
            return 0.0
            
        # Use middle finger MCP and wrist as reference line
        wrist = landmarks[0]
        middle_mcp = landmarks[9]
        
        # Calculate vector
        dx = middle_mcp.x - wrist.x
        dy = middle_mcp.y - wrist.y
        
        # Calculate angle
        angle = math.degrees(math.atan2(-dy, dx))  # Negate dy for correct orientation
        if angle < 0:
            angle += 360
            
        return angle
    
    @staticmethod
    def _distance_3d(landmark1, landmark2) -> float:
        """Calculate 3D distance between landmarks."""
        return math.sqrt(
            (landmark1.x - landmark2.x)**2 +
            (landmark1.y - landmark2.y)**2 +
            (landmark1.z - landmark2.z)**2
        )