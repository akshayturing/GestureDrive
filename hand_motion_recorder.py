# hand_motion_recorder.py
import cv2
import numpy as np
import mediapipe as mp
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HandMotionRecorder:
    """
    Records hand motions from webcam input using MediaPipe for hand landmark detection.
    Stores timestamp, position, and velocity data for all detected landmarks.
    """
    
    def __init__(self, 
                 camera_id: int = 0,
                 width: int = 640, 
                 height: int = 480, 
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5,
                 max_num_hands: int = 2,
                 record_dir: str = "recordings",
                 fps_sample_window: int = 10):
        """
        Initialize the HandMotionRecorder with camera and MediaPipe settings.
        
        Args:
            camera_id: ID of the camera to use
            width: Width for camera capture
            height: Height for camera capture
            min_detection_confidence: MediaPipe hand detection confidence threshold
            min_tracking_confidence: MediaPipe hand tracking confidence threshold
            max_num_hands: Maximum number of hands to track simultaneously
            record_dir: Directory to save recordings
            fps_sample_window: Number of frames to calculate FPS
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.max_num_hands = max_num_hands
        self.record_dir = record_dir
        
        # Ensure recording directory exists
        os.makedirs(record_dir, exist_ok=True)
        
        # Set up MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize webcam capture
        self.cap = None
        
        # Recording state variables
        self.is_recording = False
        self.current_recording = None
        self.recording_start_time = None
        self.frame_count = 0
        self.recording_name = None
        
        # FPS calculation
        self.fps_sample_window = fps_sample_window
        self.frame_times = []
        self.current_fps = 0
        
        # Hand tracking data
        self.hand_landmarks_history = []
        self.max_history_length = 300  # Store up to ~10 seconds at 30fps
        
        # Labels for recording (for training datasets)
        self.current_label = None
        
        # Debugging and visualization flags
        self.debug = False
        self.show_landmarks = True
        self.show_velocity_vectors = True
        self.mirror = True  # Mirror the image for more intuitive feedback
        
        logger.info("HandMotionRecorder initialized")
    
    def start_camera(self) -> bool:
        """
        Start the webcam capture.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}")
                return False
                
            logger.info(f"Camera {self.camera_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting camera: {str(e)}")
            return False
    
    def stop_camera(self):
        """Release the camera resource"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            logger.info("Camera released")
    
    def start_recording(self, label: str = None) -> bool:
        """
        Start recording hand motion.
        
        Args:
            label: Optional label for the recording (useful for training data)
            
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if self.is_recording:
            logger.warning("Already recording. Stop current recording first.")
            return False
            
        self.is_recording = True
        self.recording_start_time = time.time()
        self.frame_count = 0
        self.current_label = label
        
        # Generate a filename based on the current date/time and optional label
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label_suffix = f"_{label}" if label else ""
        self.recording_name = f"hand_motion_{timestamp}{label_suffix}"
        
        # Initialize the recording data structure
        self.current_recording = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "label": label,
                "camera_id": self.camera_id,
                "resolution": [self.width, self.height],
                "detection_confidence": self.min_detection_confidence,
                "tracking_confidence": self.min_tracking_confidence
            },
            "frames": []
        }
        
        # Clear previous history
        self.hand_landmarks_history = []
        
        logger.info(f"Started recording: {self.recording_name}")
        return True
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop the current recording and save it to file.
        
        Returns:
            str: Path to the saved recording file, or None if no recording was active
        """
        if not self.is_recording:
            logger.warning("Not currently recording.")
            return None
            
        self.is_recording = False
        
        # Calculate recording statistics
        duration = time.time() - self.recording_start_time
        fps = self.frame_count / duration if duration > 0 else 0
        
        # Update metadata
        self.current_recording["metadata"]["duration_seconds"] = duration
        self.current_recording["metadata"]["frame_count"] = self.frame_count
        self.current_recording["metadata"]["average_fps"] = fps
        
        # Save the recording to file
        filename = f"{self.recording_name}.json"
        filepath = os.path.join(self.record_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.current_recording, f, indent=2)
                
            logger.info(f"Recording saved to: {filepath}")
            logger.info(f"Recorded {self.frame_count} frames over {duration:.2f} seconds ({fps:.2f} fps)")
            
            # Reset recording data
            self.current_recording = None
            self.recording_start_time = None
            self.frame_count = 0
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving recording: {str(e)}")
            return None
    
    def process_frame(self, frame: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]:
        """
        Process a video frame to detect and track hand landmarks.
        If frame is None, captures from the camera.
        
        Args:
            frame: Optional video frame to process (if None, captures from camera)
            
        Returns:
            Tuple containing:
                - Processed frame with visualizations
                - Dictionary with processed data for this frame
        """
        # Capture frame from camera if not provided
        if frame is None:
            if not self.cap or not self.cap.isOpened():
                if not self.start_camera():
                    return np.zeros((self.height, self.width, 3), dtype=np.uint8), {}
                    
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Failed to capture frame from camera")
                return np.zeros((self.height, self.width, 3), dtype=np.uint8), {}
        
        # Calculate FPS
        current_time = time.time()
        self.frame_times.append(current_time)
        if len(self.frame_times) > self.fps_sample_window:
            self.frame_times.pop(0)
            
        if len(self.frame_times) >= 2:
            time_diff = self.frame_times[-1] - self.frame_times[0]
            if time_diff > 0:
                self.current_fps = (len(self.frame_times) - 1) / time_diff
        
        # Mirror the frame if needed
        if self.mirror:
            frame = cv2.flip(frame, 1)
        
        # Convert frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width, _ = rgb_frame.shape
        
        # Process with MediaPipe Hands
        with self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        ) as hands:
            results = hands.process(rgb_frame)
            
            # Frame data to be stored in recording
            frame_data = {
                "timestamp": current_time,
                "hands": []
            }
            
            # Draw hand landmarks on the frame
            if results.multi_hand_landmarks:
                for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Get handedness information
                    handedness = "unknown"
                    if results.multi_handedness and idx < len(results.multi_handedness):
                        handedness = results.multi_handedness[idx].classification[0].label
                    
                    # Extract normalized landmark coordinates
                    landmarks = []
                    for i, landmark in enumerate(hand_landmarks.landmark):
                        landmarks.append([landmark.x, landmark.y, landmark.z])
                    
                    # Calculate velocities if we have previous frames
                    velocities = []
                    
                    # Find a matching hand in the previous frame
                    if self.hand_landmarks_history and len(self.hand_landmarks_history) > 0:
                        last_frame = self.hand_landmarks_history[-1]
                        
                        # Try to match the hand based on handedness and position
                        matching_hand = None
                        for prev_hand in last_frame["hands"]:
                            if prev_hand["handedness"] == handedness:
                                matching_hand = prev_hand
                                break
                        
                        # Calculate velocities if we found a matching hand
                        if matching_hand:
                            prev_landmarks = matching_hand["landmarks"]
                            time_diff = current_time - last_frame["timestamp"]
                            
                            if time_diff > 0:
                                for i, (curr, prev) in enumerate(zip(landmarks, prev_landmarks)):
                                    # Calculate velocity in x, y, z (normalized coordinates per second)
                                    vx = (curr[0] - prev[0]) / time_diff
                                    vy = (curr[1] - prev[1]) / time_diff
                                    vz = (curr[2] - prev[2]) / time_diff
                                    
                                    # Calculate magnitude (speed)
                                    magnitude = np.sqrt(vx*vx + vy*vy + vz*vz)
                                    
                                    velocities.append({
                                        "vx": vx, "vy": vy, "vz": vz, 
                                        "magnitude": magnitude
                                    })
                    
                    # Add hand data to frame
                    hand_data = {
                        "handedness": handedness,
                        "landmarks": landmarks,
                        "velocities": velocities
                    }
                    
                    frame_data["hands"].append(hand_data)
                    
                    # Draw landmarks on the frame
                    if self.show_landmarks:
                        self.mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style()
                        )
                        
                    # Draw velocity vectors
                    if self.show_velocity_vectors and velocities:
                        self._draw_velocity_vectors(frame, hand_landmarks, velocities)
            
            # Add data to history
            self.hand_landmarks_history.append(frame_data)
            if len(self.hand_landmarks_history) > self.max_history_length:
                self.hand_landmarks_history.pop(0)
            
            # Add frame to recording if we're recording
            if self.is_recording and self.current_recording is not None:
                self.current_recording["frames"].append(frame_data)
                self.frame_count += 1
            
            # Draw recording indicator
            if self.is_recording:
                cv2.circle(frame, (30, 30), 15, (0, 0, 255), -1)  # Red circle
                cv2.putText(frame, f"REC {self.frame_count}", (50, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                if self.current_label:
                    cv2.putText(frame, f"Label: {self.current_label}", (50, 80), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Draw FPS
            cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (frame_width - 150, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            return frame, frame_data
    
    def _draw_velocity_vectors(self, frame: np.ndarray, hand_landmarks, velocities: List[Dict]):
        """Draw velocity vectors for each landmark"""
        frame_height, frame_width, _ = frame.shape
        
        # Define key landmarks to draw velocities for (to avoid clutter)
        key_landmarks = [0, 4, 8, 12, 16, 20]  # Wrist, thumb tip, finger tips
        
        for i in key_landmarks:
            if i < len(hand_landmarks.landmark) and i < len(velocities):
                landmark = hand_landmarks.landmark[i]
                velocity = velocities[i]
                
                # Get start point in pixel coordinates
                start_x = int(landmark.x * frame_width)
                start_y = int(landmark.y * frame_height)
                
                # Scale velocity to make it visible
                # The scaling factor can be adjusted based on your needs
                scale_factor = 50.0
                
                # Calculate end point
                end_x = int(start_x + velocity["vx"] * scale_factor)
                end_y = int(start_y + velocity["vy"] * scale_factor)
                
                # Color based on speed (magnitude)
                magnitude = velocity["magnitude"]
                if magnitude < 0.5:
                    color = (0, 255, 0)  # Green for slow
                elif magnitude < 2.0:
                    color = (0, 255, 255)  # Yellow for medium
                else:
                    color = (0, 0, 255)  # Red for fast
                
                # Draw the vector
                cv2.arrowedLine(frame, (start_x, start_y), (end_x, end_y), color, 2)
    
    def run_recording_session(self, duration_seconds: Optional[float] = None, 
                             label: Optional[str] = None, display: bool = True) -> Optional[str]:
        """
        Run a recording session for the specified duration or until manually stopped.
        
        Args:
            duration_seconds: How long to record (None for manual stopping)
            label: Optional label for this recording
            display: Whether to display the camera feed during recording
            
        Returns:
            str: Path to saved recording file, or None if recording failed
        """
        if not self.start_camera():
            return None
            
        if not self.start_recording(label):
            self.stop_camera()
            return None
        
        start_time = time.time()
        recording_path = None
        
        try:
            while True:
                # Process frame
                frame, _ = self.process_frame()
                
                # Display the frame
                if display:
                    cv2.imshow('Hand Motion Recorder', frame)
                
                # Check for duration expiration
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    recording_path = self.stop_recording()
                    break
                
                # Check for key press to stop
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC key
                    recording_path = self.stop_recording()
                    break
                    
            # Clean up
            if display:
                cv2.destroyAllWindows()
                
            return recording_path
            
        except Exception as e:
            logger.error(f"Error during recording session: {str(e)}")
            self.stop_recording()
            return None
        finally:
            self.stop_camera()
    
    def load_recording(self, filepath: str) -> Optional[Dict]:
        """
        Load a previously saved hand motion recording.
        
        Args:
            filepath: Path to the recording file
            
        Returns:
            Dict: The loaded recording data, or None if loading failed
        """
        try:
            with open(filepath, 'r') as f:
                recording = json.load(f)
                
            logger.info(f"Loaded recording from: {filepath}")
            return recording
            
        except Exception as e:
            logger.error(f"Error loading recording: {str(e)}")
            return None
    
    def get_recent_motion_history(self, frames_back: int = 30) -> List[Dict]:
        """
        Get the motion history for the last N frames.
        
        Args:
            frames_back: Number of past frames to retrieve
            
        Returns:
            List of frame data dictionaries
        """
        frames_back = min(frames_back, len(self.hand_landmarks_history))
        return self.hand_landmarks_history[-frames_back:]
