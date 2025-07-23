import cv2
import threading
import time
from typing import Dict, Any, Optional
import logging

class CameraProcessing:
    """
    Simplified camera processing with cleaner conditionals.
    """
    
    def __init__(self, camera, gesture_detector, motion_tracker, config_manager, event_bus):
        self.logger = logging.getLogger("CameraProcessing")
        
        # Store dependencies
        self.camera = camera
        self.gesture_detector = gesture_detector
        self.motion_tracker = motion_tracker
        self.config_manager = config_manager
        self.event_bus = event_bus
        
        # Processing state
        self.is_running = False
        self.processing_thread = None
        self.last_process_time = time.time()
        
        # Get configuration
        self.show_landmarks = self.config_manager.get("display.show_landmarks", True)
        self.gesture_cooldown = self.config_manager.get("gestures.cooldown_ms", 800) / 1000.0
        self.target_fps = self.config_manager.get("camera.fps", 30)
        
        # Current state
        self.current_gesture = self.gesture_detector.GESTURES["UNKNOWN"]
        self.current_motion = self.motion_tracker.MOTIONS["STATIONARY"]
        
        # MediaPipe drawing utilities
        self.mp_drawing = cv2.mediapipe.solutions.drawing_utils
        self.mp_drawing_styles = cv2.mediapipe.solutions.drawing_styles
        self.mp_hands = cv2.mediapipe.solutions.hands
        
        # Frame counters
        self.frame_count = 0
        self.processed_count = 0
        
        # Subscribe to config changes
        self.event_bus.subscribe("CONFIG_CHANGED", self._on_config_changed)
    
    def start(self):
        """Start processing frames."""
        if self.is_running:
            return
            
        # Make sure camera is started
        if hasattr(self.camera, 'is_running') and not self.camera.is_running:
            self.camera.start()
            
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        self.logger.info("Camera processing started")
    
    def stop(self):
        """Stop processing frames."""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
            self.processing_thread = None
        self.logger.info("Camera processing stopped")
    
    def _processing_loop(self):
        """Main processing loop running in a thread."""
        while self.is_running:
            try:
                loop_start = time.time()
                
                # Get the latest frame from the camera
                frame, fps = self.camera.get_frame()
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Increment frame counter
                self.frame_count += 1
                
                # Process the frame
                self._process_single_frame(frame)
                
                # Rate limiting to maintain target FPS
                elapsed = time.time() - loop_start
                target_time = 1.0 / self.target_fps
                
                if elapsed < target_time:
                    time.sleep(target_time - elapsed)
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {str(e)}", exc_info=True)
                time.sleep(0.1)  # Brief pause on error
    
    def _process_single_frame(self, frame):
        """
        Process a single camera frame.
        Extracted from the main loop for better organization.
        """
        try:
            # Process the frame with MediaPipe
            results = self.gesture_detector.process_frame(frame)
            
            # Create a copy for visualization/processing
            processed_frame = frame.copy()
            
            # Extract landmarks
            multi_hand_landmarks = results.get('multi_hand_landmarks')
            
            # Process hand landmarks if present
            if multi_hand_landmarks:
                self._process_hand_landmarks(processed_frame, multi_hand_landmarks, results)
            else:
                # No hands detected, revert to stationary for motion
                self.current_motion = self.motion_tracker.MOTIONS["STATIONARY"]
            
            # Always publish the processed frame
            self._publish_processed_frame(processed_frame)
            
            # Increment processed frame counter
            self.processed_count += 1
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {str(e)}", exc_info=True)
    
    def _process_hand_landmarks(self, frame, multi_hand_landmarks, results):
        """
        Process detected hand landmarks.
        Handles gesture recognition and motion tracking.
        """
        # Track landmarks for motion detection
        self.motion_tracker.add_landmarks(multi_hand_landmarks)
        
        # Check if we should process gesture (respect cooldown)
        current_time = time.time()
        if current_time - self.last_process_time > self.gesture_cooldown:
            # Process each hand (using first hand for now)
            hand_landmarks = multi_hand_landmarks[0]
            
            # Get gesture
            self._process_gesture(hand_landmarks)
            
            # Get motion
            self._process_motion()
            
            # Reset cooldown timer
            self.last_process_time = current_time
        
        # Draw hand landmarks if enabled
        if self.show_landmarks:
            self._draw_landmarks(frame, multi_hand_landmarks)
    
    def _process_gesture(self, hand_landmarks):
        """
        Process and publish gesture events.
        """
        # Get gesture
        gesture = self.gesture_detector.update_gesture(hand_landmarks)
        
        # Only publish if gesture changed
        if gesture != self.current_gesture:
            self.current_gesture = gesture
            
            # Publish gesture event
            self.event_bus.publish("gesture_detected", {
                'gesture': gesture,
                'label': self.gesture_detector.get_gesture_label(gesture),
                'timestamp': time.time(),
                'confidence': getattr(self.gesture_detector, 'last_confidence', 0.8)
            })
    
    def _process_motion(self):
        """
        Process and publish motion events.
        """
        # Detect motion gesture
        motion = self.motion_tracker.detect_motion_gesture(
            threshold=self.config_manager.get("motion.threshold", 0.15)
        )
        
        # Only publish if significant motion detected and changed
        is_significant = (motion != self.motion_tracker.MOTIONS["STATIONARY"] and 
                         motion != self.motion_tracker.MOTIONS["INSUFFICIENT_DATA"])
                         
        if motion != self.current_motion and is_significant:
            self.current_motion = motion
            
            # Get velocity statistics
            velocity_stats = self.motion_tracker.get_velocity_stats()
            
            # Publish motion event
            self.event_bus.publish("motion_detected", {
                'motion': motion,
                'label': self.motion_tracker.get_motion_label(motion),
                'velocity': velocity_stats,
                'timestamp': time.time()
            })
    
    def _draw_landmarks(self, frame, multi_hand_landmarks):
        """Draw hand landmarks and information on frame."""
        # Draw landmarks
        for hand_landmarks in multi_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style())
        
        # Add text overlays
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        color = (0, 255, 0)
        
        # Show current gesture and motion
        cv2.putText(
            frame, 
            f"Gesture: {self.gesture_detector.get_gesture_label(self.current_gesture)}", 
            (10, 30), font, font_scale, color, thickness)
            
        cv2.putText(
            frame, 
            f"Motion: {self.motion_tracker.get_motion_label(self.current_motion)}", 
            (10, 60), font, font_scale, color, thickness)
        
        # Show FPS if enabled
        if self.config_manager.get("display.show_fps", True):
            fps_text = f"FPS: {getattr(self.camera, 'fps', 0):.1f}"
            cv2.putText(frame, fps_text, (10, 90), font, font_scale, color, thickness)
    
    def _publish_processed_frame(self, processed_frame):
        """Publish the processed frame."""
        self.event_bus.publish("frame_processed", {
            'frame': processed_frame,
            'fps': getattr(self.camera, 'fps', 0),
            'gesture': self.current_gesture,
            'motion': self.current_motion,
            'frame_count': self.frame_count,
            'processed_count': self.processed_count
        })
    
    def set_show_landmarks(self, show_landmarks):
        """Enable or disable showing landmarks on the frame."""
        self.show_landmarks = show_landmarks
    
    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about current processing state."""
        return {
            'is_running': self.is_running,
            'current_gesture': self.current_gesture,
            'gesture_label': self.gesture_detector.get_gesture_label(self.current_gesture),
            'current_motion': self.current_motion,
            'motion_label': self.motion_tracker.get_motion_label(self.current_motion),
            'show_landmarks': self.show_landmarks,
            'gesture_cooldown': self.gesture_cooldown,
            'last_process_time': self.last_process_time,
            'frame_count': self.frame_count,
            'processed_count': self.processed_count,
            'processing_fps': self.processed_count / (time.time() - self.last_process_time)
                              if time.time() - self.last_process_time > 0 else 0
        }
        
    def _on_config_changed(self, change_data):
        """Handle configuration changes."""
        try:
            key = change_data.get("key", "")
            new_value = change_data.get("new_value")
            
            # Update settings based on config changes
            if key == "display.show_landmarks":
                self.show_landmarks = new_value
                self.logger.info(f"Updated show_landmarks setting to {new_value}")
                
            elif key == "gestures.cooldown_ms" and new_value is not None:
                self.gesture_cooldown = new_value / 1000.0
                self.logger.info(f"Updated gesture cooldown to {self.gesture_cooldown} seconds")
                
            elif key == "camera.fps" and new_value is not None:
                self.target_fps = new_value
                self.logger.info(f"Updated target processing FPS to {new_value}")
                
        except Exception as e:
            self.logger.error(f"Error handling config change: {str(e)}")