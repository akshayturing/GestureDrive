# gesture_detector.py
import math
import time
import numpy as np
from profiling.performance_profiler import performance_tracker

class SelectionGestureDetector:
    """Detects and tracks tap and pinch gestures for file selection"""
    
    def __init__(self, cooldown_period=0.8):
        self.last_landmark_positions = []
        self.position_history = []  # Store recent hand positions
        self.depth_history = []     # Store Z-coordinate changes for tap detection
        self.history_size = 10
        self.last_gesture_time = 0
        self.cooldown_period = cooldown_period
        
    @performance_tracker.time_it(category="gesture_processing")
    def process_frame(self, frame):
        """Process a frame to detect hands and landmarks."""
        # Convert to RGB for MediaPipe (measure conversion time)
        convert_start = time.time()
        rgb_frame = frame.copy()
        if len(frame.shape) == 3:  # Color image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        convert_time = time.time() - convert_start
        
        # Process with MediaPipe (measure MediaPipe processing time)
        mediapipe_start = time.time()
        results = self.hands.process(rgb_frame)
        mediapipe_time = time.time() - mediapipe_start
        
        # Log performance statistics
        if self.performance_logging and frame_count % 30 == 0:  # Log every 30 frames
            logger.debug(f"Gesture detector: Convert: {convert_time*1000:.1f}ms, MediaPipe: {mediapipe_time*1000:.1f}ms")
        
        return {
            'multi_hand_landmarks': results.multi_hand_landmarks,
            'multi_handedness': results.multi_handedness
        }
    
    @performance_tracker.time_it(category="gesture_recognition") 
    def update(self, hand_landmarks):
        """
        Update the detector with new hand landmark data
        Returns detected gesture: 'tap', 'pinch', or None
        """
        if not hand_landmarks:
            return None
            
        # Get current time to enforce cooldown
        current_time = time.time()
        if current_time - self.last_gesture_time < self.cooldown_period:
            return None
            
        # Extract key landmarks (index finger and thumb)
        index_tip = hand_landmarks[0].landmark[8]
        thumb_tip = hand_landmarks[0].landmark[4]
        
        # Store landmark histories
        self._update_histories(index_tip, thumb_tip)
        
        # Detect pinch gesture
        pinch_detected = self._detect_pinch(thumb_tip, index_tip)
        if pinch_detected:
            self.last_gesture_time = current_time
            return "pinch"
            
        # Detect tap gesture
        tap_detected = self._detect_tap()
        if tap_detected:
            self.last_gesture_time = current_time
            return "tap"
            
        return None
    
    def _update_histories(self, index_tip, thumb_tip):
        """Update position and depth histories"""
        # Add current positions to history
        self.position_history.append((index_tip, thumb_tip))
        if len(self.position_history) > self.history_size:
            self.position_history.pop(0)
            
        # Track z-coordinate of index finger for tap detection
        self.depth_history.append(index_tip.z)
        if len(self.depth_history) > self.history_size:
            self.depth_history.pop(0)
    
    def _detect_pinch(self, thumb_tip, index_tip):
        """Detect pinch gesture based on thumb and index finger proximity"""
        # Calculate 3D Euclidean distance between thumb and index finger tips
        distance = math.sqrt(
            (thumb_tip.x - index_tip.x) ** 2 +
            (thumb_tip.y - index_tip.y) ** 2 +
            (thumb_tip.z - index_tip.z) ** 2
        )
        
        # Pinch is detected if distance is very small (threshold value may need calibration)
        pinch_threshold = 0.05  # Adjusted based on MediaPipe's normalized coordinates
        return distance < pinch_threshold
    
    def _detect_tap(self):
        """
        Detect tap gesture based on forward-backward motion of index finger
        A tap is a quick forward motion (decreasing Z) followed by backward motion (increasing Z)
        """
        if len(self.depth_history) < 5:  # Need enough history to detect pattern
            return False
            
        # Get recent depth values
        recent_depths = self.depth_history[-5:]
        
        # Calculate changes in depth
        depth_changes = [recent_depths[i] - recent_depths[i-1] for i in range(1, len(recent_depths))]
        
        # Define tap pattern: forward motion (negative z change) followed by backward motion (positive z change)
        # The sum of absolute changes should also exceed a threshold to avoid detecting small movements
        tap_threshold = 0.05
        
        # Pattern: significant forward motion followed by backward motion
        forward_motion = any(change < -tap_threshold for change in depth_changes[:2])
        backward_motion = any(change > tap_threshold for change in depth_changes[2:])
        
        return forward_motion and backward_motion
