# # gesture_detector.py
# import math
# import time
# import numpy as np
# from profiling.performance_profiler import performance_tracker

# class SelectionGestureDetector:
#     """Detects and tracks tap and pinch gestures for file selection"""
    
#     def __init__(self, cooldown_period=0.8):
#         self.last_landmark_positions = []
#         self.position_history = []  # Store recent hand positions
#         self.depth_history = []     # Store Z-coordinate changes for tap detection
#         self.history_size = 10
#         self.last_gesture_time = 0
#         self.cooldown_period = cooldown_period
        
#     @performance_tracker.time_it(category="gesture_processing")
#     def process_frame(self, frame):
#         """Process a frame to detect hands and landmarks."""
#         # Convert to RGB for MediaPipe (measure conversion time)
#         convert_start = time.time()
#         rgb_frame = frame.copy()
#         if len(frame.shape) == 3:  # Color image
#             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         convert_time = time.time() - convert_start
        
#         # Process with MediaPipe (measure MediaPipe processing time)
#         mediapipe_start = time.time()
#         results = self.hands.process(rgb_frame)
#         mediapipe_time = time.time() - mediapipe_start
        
#         # Log performance statistics
#         if self.performance_logging and frame_count % 30 == 0:  # Log every 30 frames
#             logger.debug(f"Gesture detector: Convert: {convert_time*1000:.1f}ms, MediaPipe: {mediapipe_time*1000:.1f}ms")
        
#         return {
#             'multi_hand_landmarks': results.multi_hand_landmarks,
#             'multi_handedness': results.multi_handedness
#         }
    
#     @performance_tracker.time_it(category="gesture_recognition") 
#     def update(self, hand_landmarks):
#         """
#         Update the detector with new hand landmark data
#         Returns detected gesture: 'tap', 'pinch', or None
#         """
#         if not hand_landmarks:
#             return None
            
#         # Get current time to enforce cooldown
#         current_time = time.time()
#         if current_time - self.last_gesture_time < self.cooldown_period:
#             return None
            
#         # Extract key landmarks (index finger and thumb)
#         index_tip = hand_landmarks[0].landmark[8]
#         thumb_tip = hand_landmarks[0].landmark[4]
        
#         # Store landmark histories
#         self._update_histories(index_tip, thumb_tip)
        
#         # Detect pinch gesture
#         pinch_detected = self._detect_pinch(thumb_tip, index_tip)
#         if pinch_detected:
#             self.last_gesture_time = current_time
#             return "pinch"
            
#         # Detect tap gesture
#         tap_detected = self._detect_tap()
#         if tap_detected:
#             self.last_gesture_time = current_time
#             return "tap"
            
#         return None
    
#     def _update_histories(self, index_tip, thumb_tip):
#         """Update position and depth histories"""
#         # Add current positions to history
#         self.position_history.append((index_tip, thumb_tip))
#         if len(self.position_history) > self.history_size:
#             self.position_history.pop(0)
            
#         # Track z-coordinate of index finger for tap detection
#         self.depth_history.append(index_tip.z)
#         if len(self.depth_history) > self.history_size:
#             self.depth_history.pop(0)
    
#     def _detect_pinch(self, thumb_tip, index_tip):
#         """Detect pinch gesture based on thumb and index finger proximity"""
#         # Calculate 3D Euclidean distance between thumb and index finger tips
#         distance = math.sqrt(
#             (thumb_tip.x - index_tip.x) ** 2 +
#             (thumb_tip.y - index_tip.y) ** 2 +
#             (thumb_tip.z - index_tip.z) ** 2
#         )
        
#         # Pinch is detected if distance is very small (threshold value may need calibration)
#         pinch_threshold = 0.05  # Adjusted based on MediaPipe's normalized coordinates
#         return distance < pinch_threshold
    
#     def _detect_tap(self):
#         """
#         Detect tap gesture based on forward-backward motion of index finger
#         A tap is a quick forward motion (decreasing Z) followed by backward motion (increasing Z)
#         """
#         if len(self.depth_history) < 5:  # Need enough history to detect pattern
#             return False
            
#         # Get recent depth values
#         recent_depths = self.depth_history[-5:]
        
#         # Calculate changes in depth
#         depth_changes = [recent_depths[i] - recent_depths[i-1] for i in range(1, len(recent_depths))]
        
#         # Define tap pattern: forward motion (negative z change) followed by backward motion (positive z change)
#         # The sum of absolute changes should also exceed a threshold to avoid detecting small movements
#         tap_threshold = 0.05
        
#         # Pattern: significant forward motion followed by backward motion
#         forward_motion = any(change < -tap_threshold for change in depth_changes[:2])
#         backward_motion = any(change > tap_threshold for change in depth_changes[2:])
        
#         return forward_motion and backward_motion
# core/gesture_detector.py
import math
import cv2
import mediapipe as mp
from typing import Dict, Any, List, Optional, Tuple
import logging
import numpy as np

from utils.gesture_utils import GestureUtils

class GestureDetector:
    """
    Refactored gesture detector with simplified conditionals.
    """
    
    # Define gesture types for consistent reference
    GESTURES = {
        "UNKNOWN": "unknown",
        "FIST": "fist",
        "OPEN_PALM": "open_palm",
        "POINT_UP": "point_up",
        "POINT_DOWN": "point_down",
        "POINT_LEFT": "point_left",
        "POINT_RIGHT": "point_right",
        "THUMBS_UP": "thumbs_up",
        "THUMBS_DOWN": "thumbs_down",
        "OK": "ok",
        "PEACE": "peace"
    }
    
    def __init__(self, min_detection_confidence=0.7, min_tracking_confidence=0.5, max_num_hands=2):
        self.logger = logging.getLogger("GestureDetector")
        
        # Initialize MediaPipe Hands
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # Gesture recognition state
        self.gesture_buffer = []
        self.buffer_size = 5  # Number of frames for smoothing
        self.current_gesture = self.GESTURES["UNKNOWN"]
        self.last_confidence = 0.0
        
        # Map gesture names to human-readable labels
        self.gesture_labels = {
            self.GESTURES["POINT_UP"]: "Point Up",
            self.GESTURES["POINT_DOWN"]: "Point Down",
            self.GESTURES["POINT_LEFT"]: "Point Left", 
            self.GESTURES["POINT_RIGHT"]: "Point Right",
            self.GESTURES["FIST"]: "Fist",
            self.GESTURES["OPEN_PALM"]: "Open Palm",
            self.GESTURES["THUMBS_UP"]: "Thumbs Up",
            self.GESTURES["THUMBS_DOWN"]: "Thumbs Down",
            self.GESTURES["OK"]: "OK",
            self.GESTURES["PEACE"]: "Peace",
            self.GESTURES["UNKNOWN"]: "Unknown"
        }
    
    def process_frame(self, frame) -> Dict[str, Any]:
        """
        Process a frame to detect hands and landmarks.
        """
        # Convert to RGB for MediaPipe
        rgb_frame = frame.copy()
        if len(frame.shape) == 3:  # Color image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = self.hands.process(rgb_frame)
        
        return {
            'multi_hand_landmarks': results.multi_hand_landmarks,
            'multi_handedness': results.multi_handedness
        }
    
    def recognize_gesture(self, hand_landmarks) -> Dict[str, Any]:
        """
        Identify the static hand gesture from landmarks.
        
        Returns:
            Dictionary with gesture type and confidence
        """
        if not hand_landmarks:
            return {"gesture": self.GESTURES["UNKNOWN"], "confidence": 0.0}
        
        # Get extension state for all fingers at once
        extension_state = GestureUtils.get_finger_extension_state(hand_landmarks.landmark)
        
        # Simple lookup dictionary for gesture patterns
        # Maps finger extension patterns to gestures
        gesture_patterns = {
            # Format: (thumb, index, middle, ring, pinky) -> gesture
            (False, False, False, False, False): self.GESTURES["FIST"],
            (True, True, True, True, True): self.GESTURES["OPEN_PALM"],
            (False, True, False, False, False): "pointing",  # Need direction
            (False, True, True, False, False): self.GESTURES["PEACE"],
            (True, True, False, False, False): self.GESTURES["OK"],
            (True, False, False, False, False): "thumbs",  # Need orientation
        }
        
        # Create pattern key from extension state
        pattern = (extension_state["thumb"], extension_state["index"], 
                  extension_state["middle"], extension_state["ring"], 
                  extension_state["pinky"])
        
        # Initial confidence - will refine based on additional checks
        confidence = 0.7
        
        # Look up the gesture
        gesture = gesture_patterns.get(pattern, self.GESTURES["UNKNOWN"])
        
        # For pointing gestures, determine direction
        if gesture == "pointing":
            gesture = GestureUtils.get_pointing_direction(hand_landmarks.landmark)
            confidence = 0.85  # Higher confidence for directional gestures
        
        # For thumbs gestures, determine orientation
        elif gesture == "thumbs":
            orientation = GestureUtils.calculate_hand_orientation(hand_landmarks.landmark)
            if 45 <= orientation <= 135:  # Roughly upward
                gesture = self.GESTURES["THUMBS_UP"]
            elif 225 <= orientation <= 315:  # Roughly downward
                gesture = self.GESTURES["THUMBS_DOWN"]
            else:
                gesture = self.GESTURES["UNKNOWN"]
                confidence = 0.5  # Lower confidence if orientation is ambiguous
        
        # Store confidence for external reference
        self.last_confidence = confidence
        
        return {"gesture": gesture, "confidence": confidence}
    
    def update_gesture(self, hand_landmarks) -> str:
        """
        Update current gesture with temporal smoothing.
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            
        Returns:
            Current recognized gesture
        """
        if not hand_landmarks:
            return self.GESTURES["UNKNOWN"]
            
        # Get new gesture
        gesture_result = self.recognize_gesture(hand_landmarks)
        gesture = gesture_result["gesture"]
        
        # Add to buffer for temporal smoothing
        self.gesture_buffer.append(gesture)
        if len(self.gesture_buffer) > self.buffer_size:
            self.gesture_buffer.pop(0)
        
        # Only update when we have enough samples
        if len(self.gesture_buffer) >= 3:
            # Count occurrences of each gesture using Counter (more efficient)
            from collections import Counter
            gesture_counts = Counter(self.gesture_buffer)
            
            # Get most common gesture and its count
            most_common = gesture_counts.most_common(1)[0]
            
            # Only update if the gesture appears at least 60% of the time
            if most_common[1] >= len(self.gesture_buffer) * 0.6:
                self.current_gesture = most_common[0]
        
        return self.current_gesture
    
    def get_gesture_label(self, gesture=None) -> str:
        """
        Convert gesture to human-readable label.
        """
        if gesture is None:
            gesture = self.current_gesture
        
        return self.gesture_labels.get(gesture, "Unknown Gesture")