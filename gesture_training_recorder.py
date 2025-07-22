# gesture_training_recorder.py
import cv2
import numpy as np
import mediapipe as mp
import time
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GestureTrainingRecorder:
    """
    Specialized recorder for gesture training sessions that captures a 
    continuous flow of hand keypoints and timestamps for custom gesture definition.
    """
    
    def __init__(self, 
                 camera_id: int = 0,
                 width: int = 640, 
                 height: int = 480, 
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5,
                 training_dir: str = "training_data",
                 required_examples: int = 5):
        """
        Initialize the GestureTrainingRecorder with camera and training settings.
        
        Args:
            camera_id: ID of the camera to use
            width: Width for camera capture
            height: Height for camera capture
            min_detection_confidence: MediaPipe hand detection confidence threshold
            min_tracking_confidence: MediaPipe hand tracking confidence threshold
            training_dir: Directory to save training data
            required_examples: Number of examples needed per gesture
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.training_dir = training_dir
        self.required_examples = required_examples
        
        # Ensure training directory exists
        os.makedirs(training_dir, exist_ok=True)
        
        # Set up MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize webcam capture
        self.cap = None
        
        # Training session state
        self.current_gesture_name = None
        self.current_session_id = None
        self.examples_recorded = 0
        self.session_start_time = None
        
        # Recording state for individual examples
        self.is_recording_example = False
        self.current_example_data = None
        self.example_start_time = None
        self.current_example_id = None
        
        # Quality metrics
        self.min_frames_per_example = 15  # Minimum frames for a valid example
        self.max_example_duration = 5.0   # Maximum duration in seconds
        self.min_movement_threshold = 0.05  # Minimum movement required
        
        # Visual feedback settings
        self.show_landmarks = True
        self.show_hand_orientation = True
        self.show_progress_bar = True
        self.mirror = True
        
        logger.info("GestureTrainingRecorder initialized")
    
    def start_camera(self) -> bool:
        """Start the webcam capture."""
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
    
    def start_training_session(self, gesture_name: str) -> bool:
        """
        Start a new gesture training session.
        
        Args:
            gesture_name: Name of the gesture to train
            
        Returns:
            bool: True if session started successfully
        """
        if not gesture_name or not gesture_name.strip():
            logger.error("Gesture name cannot be empty")
            return False
            
        # Clean the gesture name for file system use
        safe_gesture_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' 
                                   for c in gesture_name.strip().lower())
        
        # Generate a unique session ID
        session_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = f"{safe_gesture_name}_{timestamp}_{session_id}"
        
        # Create session directory
        session_dir = os.path.join(self.training_dir, self.current_session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Initialize session state
        self.current_gesture_name = gesture_name
        self.examples_recorded = 0
        self.session_start_time = time.time()
        
        # Create session metadata file
        metadata = {
            "gesture_name": gesture_name,
            "safe_gesture_name": safe_gesture_name,
            "session_id": self.current_session_id,
            "start_time": self.session_start_time,
            "timestamp": datetime.now().isoformat(),
            "required_examples": self.required_examples,
            "examples_recorded": 0,
            "examples": []
        }
        
        with open(os.path.join(session_dir, "session_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Started training session for gesture '{gesture_name}'")
        return True
    
    def end_training_session(self) -> Optional[str]:
        """
        End the current training session and compile the results.
        
        Returns:
            str: Path to the session directory or None if no session was active
        """
        if not self.current_session_id:
            logger.warning("No active training session")
            return None
            
        session_dir = os.path.join(self.training_dir, self.current_session_id)
        
        # Update metadata
        metadata_path = os.path.join(session_dir, "session_metadata.json")
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                
            metadata["end_time"] = time.time()
            metadata["duration_seconds"] = metadata["end_time"] - metadata["start_time"]
            metadata["examples_recorded"] = self.examples_recorded
            metadata["completed"] = self.examples_recorded >= self.required_examples
            
            # Get list of all example files
            example_files = [f for f in os.listdir(session_dir) 
                            if f.startswith("example_") and f.endswith(".json")]
            metadata["examples"] = example_files
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
                
            # Create a summary file with examples data combined
            self._compile_training_data(session_dir)
                
        except Exception as e:
            logger.error(f"Error updating session metadata: {str(e)}")
        
        logger.info(f"Ended training session with {self.examples_recorded} examples recorded")
        
        # Reset session state
        session_id = self.current_session_id
        self.current_session_id = None
        self.current_gesture_name = None
        self.examples_recorded = 0
        self.session_start_time = None
        
        return session_dir
    
    def _compile_training_data(self, session_dir: str):
        """Compile all examples into a single training data file"""
        example_files = sorted([f for f in os.listdir(session_dir) 
                               if f.startswith("example_") and f.endswith(".json")])
        
        if not example_files:
            logger.warning("No examples to compile")
            return
            
        examples_data = []
        
        for file in example_files:
            try:
                with open(os.path.join(session_dir, file), "r") as f:
                    example = json.load(f)
                examples_data.append(example)
            except Exception as e:
                logger.error(f"Error loading example {file}: {str(e)}")
        
        # Create combined training data
        training_data = {
            "gesture_name": self.current_gesture_name,
            "created": datetime.now().isoformat(),
            "example_count": len(examples_data),
            "examples": examples_data
        }
        
        # Save to file
        with open(os.path.join(session_dir, "training_data.json"), "w") as f:
            json.dump(training_data, f, indent=2)
            
        logger.info(f"Compiled {len(examples_data)} examples into training data")
    
    def start_example_recording(self) -> bool:
        """
        Start recording a new example for the current gesture.
        
        Returns:
            bool: True if recording started successfully
        """
        if not self.current_session_id:
            logger.error("No active training session")
            return False
            
        if self.is_recording_example:
            logger.warning("Already recording an example")
            return False
            
        # Generate a unique example ID
        self.current_example_id = f"example_{self.examples_recorded + 1:02d}"
        
        # Initialize example data
        self.current_example_data = {
            "example_id": self.current_example_id,
            "gesture_name": self.current_gesture_name,
            "start_time": time.time(),
            "timestamp": datetime.now().isoformat(),
            "frames": []
        }
        
        self.example_start_time = time.time()
        self.is_recording_example = True
        
        logger.info(f"Started recording example {self.current_example_id}")
        return True
    
    def stop_example_recording(self) -> Optional[Dict]:
        """
        Stop recording the current example and save it.
        
        Returns:
            dict: Example data if recording was active, None otherwise
        """
        if not self.is_recording_example or not self.current_example_data:
            logger.warning("No active example recording")
            return None
            
        # Stop recording
        self.is_recording_example = False
        
        # Update example metadata
        self.current_example_data["end_time"] = time.time()
        self.current_example_data["duration_seconds"] = (
            self.current_example_data["end_time"] - self.current_example_data["start_time"]
        )
        self.current_example_data["frame_count"] = len(self.current_example_data["frames"])
        
        # Check if the example meets quality requirements
        quality_check = self._check_example_quality(self.current_example_data)
        self.current_example_data["quality_check"] = quality_check
        
        # Save the example if it's valid
        if quality_check["is_valid"]:
            self._save_example(self.current_example_data)
            self.examples_recorded += 1
            logger.info(f"Recorded valid example {self.current_example_id} with {self.current_example_data['frame_count']} frames")
        else:
            logger.warning(f"Example {self.current_example_id} failed quality check: {quality_check['reason']}")
        
        # Store a copy of the example data before resetting
        example_data = self.current_example_data
        
        # Reset recording state
        self.current_example_data = None
        self.example_start_time = None
        self.current_example_id = None
        
        return example_data
    
    def _check_example_quality(self, example_data: Dict) -> Dict:
        """
        Check if an example meets quality requirements.
        
        Returns:
            dict: Quality check results
        """
        frames = example_data.get("frames", [])
        duration = example_data.get("duration_seconds", 0)
        
        # Check minimum frame count
        if len(frames) < self.min_frames_per_example:
            return {
                "is_valid": False,
                "reason": f"Too few frames: {len(frames)} (minimum: {self.min_frames_per_example})"
            }
            
        # Check maximum duration
        if duration > self.max_example_duration:
            return {
                "is_valid": False,
                "reason": f"Recording too long: {duration:.2f}s (maximum: {self.max_example_duration}s)"
            }
            
        # Check for sufficient movement (using wrist point)
        if len(frames) >= 2:
            # Get wrist positions
            wrist_positions = []
            for frame in frames:
                if frame.get("landmarks") and len(frame["landmarks"]) > 0:
                    wrist = frame["landmarks"][0]  # First landmark is the wrist
                    wrist_positions.append((wrist[0], wrist[1]))
            
            # Calculate maximum distance moved
            if wrist_positions:
                max_distance = 0
                for i in range(len(wrist_positions)):
                    for j in range(i+1, len(wrist_positions)):
                        p1 = wrist_positions[i]
                        p2 = wrist_positions[j]
                        distance = np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                        max_distance = max(max_distance, distance)
                
                if max_distance < self.min_movement_threshold:
                    return {
                        "is_valid": False,
                        "reason": f"Insufficient movement: {max_distance:.3f} (minimum: {self.min_movement_threshold})"
                    }
        
        # All checks passed
        return {
            "is_valid": True,
            "frame_count": len(frames),
            "duration_seconds": duration
        }
    
    def _save_example(self, example_data: Dict):
        """Save an example to the session directory"""
        if not self.current_session_id:
            logger.error("No active training session")
            return
            
        session_dir = os.path.join(self.training_dir, self.current_session_id)
        example_file = f"{example_data['example_id']}.json"
        
        # Save the example file
        with open(os.path.join(session_dir, example_file), "w") as f:
            json.dump(example_data, f, indent=2)
            
        # Update session metadata
        metadata_path = os.path.join(session_dir, "session_metadata.json")
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                
            metadata["examples_recorded"] = self.examples_recorded
            if "examples" not in metadata:
                metadata["examples"] = []
            metadata["examples"].append(example_file)
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating session metadata: {str(e)}")
    
    def process_frame(self, frame: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict]:
        """
        Process a video frame to detect hand landmarks and update training data.
        
        Args:
            frame: Video frame to process (if None, captures from camera)
            
        Returns:
            Tuple containing:
                - Processed frame with visualizations
                - Frame data dictionary
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
        
        # Mirror the frame if needed
        if self.mirror:
            frame = cv2.flip(frame, 1)
        
        # Convert frame to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width, _ = rgb_frame.shape
        
        # Process with MediaPipe Hands
        with self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,  # Focus on one hand for training
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        ) as hands:
            results = hands.process(rgb_frame)
            
            # Frame data to be stored
            frame_data = {
                "timestamp": time.time(),
                "landmarks": None,
                "handedness": None
            }
            
            # Process hand landmarks
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]  # Use first hand
                
                # Convert landmarks to simple list format
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append([lm.x, lm.y, lm.z])
                frame_data["landmarks"] = landmarks
                
                # Get handedness
                if results.multi_handedness:
                    frame_data["handedness"] = results.multi_handedness[0].classification[0].label
                
                # Draw landmarks on the frame
                if self.show_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing_styles.get_default_hand_landmarks_style(),
                        self.mp_drawing_styles.get_default_hand_connections_style()
                    )
                    
                # Draw hand orientation if enabled
                if self.show_hand_orientation:
                    self._draw_hand_orientation(frame, hand_landmarks)
            
            # Add frame to the example data if we're recording
            if self.is_recording_example and self.current_example_data is not None:
                if frame_data["landmarks"]:  # Only add frames with detected hands
                    self.current_example_data["frames"].append(frame_data)
            
            # Add recording UI elements
            self._add_training_ui(frame, frame_data)
            
            return frame, frame_data
    
    def _draw_hand_orientation(self, frame: np.ndarray, hand_landmarks):
        """Draw hand orientation indicators (palm direction, etc.)"""
        frame_height, frame_width, _ = frame.shape
        
        # Get key landmarks
        wrist = hand_landmarks.landmark[0]
        index_mcp = hand_landmarks.landmark[5]
        pinky_mcp = hand_landmarks.landmark[17]
        middle_tip = hand_landmarks.landmark[12]
        
        # Convert to pixel coordinates
        wrist_px = (int(wrist.x * frame_width), int(wrist.y * frame_height))
        index_mcp_px = (int(index_mcp.x * frame_width), int(index_mcp.y * frame_height))
        pinky_mcp_px = (int(pinky_mcp.x * frame_width), int(pinky_mcp.y * frame_height))
        middle_tip_px = (int(middle_tip.x * frame_width), int(middle_tip.y * frame_height))
        
        # Draw palm normal (perpendicular vector to palm plane)
        # First, get the palm vector from index to pinky MCP
        palm_vector = np.array([pinky_mcp_px[0] - index_mcp_px[0], 
                              pinky_mcp_px[1] - index_mcp_px[1]])
        palm_center = ((index_mcp_px[0] + pinky_mcp_px[0]) // 2,
                     (index_mcp_px[1] + pinky_mcp_px[1]) // 2)
        
        # Draw palm center
        cv2.circle(frame, palm_center, 5, (255, 0, 0), -1)
        
        # Draw palm direction vector
        palm_length = 50  # Length of the arrow
        palm_dir_end = (int(palm_center[0] + palm_vector[0] / np.linalg.norm(palm_vector) * palm_length),
                     int(palm_center[1] + palm_vector[1] / np.linalg.norm(palm_vector) * palm_length))
        cv2.arrowedLine(frame, palm_center, palm_dir_end, (0, 255, 0), 2)
        
        # Draw pointing direction (wrist to middle finger)
        point_vector = np.array([middle_tip_px[0] - wrist_px[0],
                              middle_tip_px[1] - wrist_px[1]])
        point_length = 100  # Length of the arrow
        point_dir_end = (int(wrist_px[0] + point_vector[0] / np.linalg.norm(point_vector) * point_length),
                      int(wrist_px[1] + point_vector[1] / np.linalg.norm(point_vector) * point_length))
        cv2.arrowedLine(frame, wrist_px, point_dir_end, (0, 0, 255), 2)
    
    def _add_training_ui(self, frame: np.ndarray, frame_data: Dict):
        """Add training UI elements to the frame"""
        height, width, _ = frame.shape
        
        # Add session status at the top
        if self.current_gesture_name:
            cv2.rectangle(frame, (0, 0), (width, 60), (0, 0, 0), -1)
            cv2.putText(frame, f"Training: {self.current_gesture_name}", 
                      (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Examples: {self.examples_recorded}/{self.required_examples}", 
                      (width - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add recording indicator
        if self.is_recording_example:
            # Elapsed time for current example
            elapsed = time.time() - self.example_start_time
            remaining = max(0, self.max_example_duration - elapsed)
            
            # Red recording circle
            cv2.circle(frame, (30, height - 30), 15, (0, 0, 255), -1)
            
            # Recording text
            cv2.putText(frame, f"Recording example {self.examples_recorded + 1}", 
                      (60, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Progress bar for recording time
            if self.show_progress_bar:
                progress = min(1.0, elapsed / self.max_example_duration)
                bar_width = int(width * 0.6)
                bar_height = 20
                bar_x = (width - bar_width) // 2
                bar_y = height - 70
                
                # Background bar
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                            (100, 100, 100), -1)
                
                # Progress bar
                progress_width = int(bar_width * progress)
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), 
                            (0, 255, 0) if progress < 0.8 else (0, 165, 255) if progress < 0.9 else (0, 0, 255), -1)
                
                # Time text
                cv2.putText(frame, f"{remaining:.1f}s", (bar_x + bar_width + 10, bar_y + 15), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        else:
            # Instructions when not recording
            if self.current_gesture_name:
                if self.examples_recorded < self.required_examples:
                    instruction = "Press SPACE to record an example"
                else:
                    instruction = "All examples recorded! Press ESC to finish"
                
                # Put instruction at the bottom of the frame
                text_size = cv2.getTextSize(instruction, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                text_x = (width - text_size[0]) // 2
                cv2.putText(frame, instruction, (text_x, height - 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Hand detected indicator
        if "landmarks" in frame_data and frame_data["landmarks"]:
            cv2.putText(frame, "Hand Detected", (width - 150, 60), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No Hand", (width - 150, 60), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    def run_training_session(self, gesture_name: str) -> Optional[str]:
        """
        Run a complete training session for a gesture.
        
        Args:
            gesture_name: Name of the gesture to train
            
        Returns:
            str: Path to the session directory, or None if training was cancelled
        """
        if not self.start_camera():
            return None
            
        if not self.start_training_session(gesture_name):
            self.stop_camera()
            return None
        
        # Create window
        window_name = f"Gesture Training: {gesture_name}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        try:
            while True:
                # Process frame
                frame, frame_data = self.process_frame()
                
                # Display the frame
                cv2.imshow(window_name, frame)
                
                # Process key events
                key = cv2.waitKey(1) & 0xFF
                
                if key == 27:  # ESC - end session
                    session_dir = self.end_training_session()
                    break
                    
                elif key == ord(' '):  # SPACE - start/stop example recording
                    if self.is_recording_example:
                        self.stop_example_recording()
                    elif self.examples_recorded < self.required_examples:
                        self.start_example_recording()
                
                # Check if all required examples have been collected
                if self.examples_recorded >= self.required_examples:
                    # Auto-end session if we've reached required examples
                    # but let the user end it manually if they want to collect more
                    pass
                
                # Check if the example recording has exceeded maximum duration
                if (self.is_recording_example and 
                    time.time() - self.example_start_time > self.max_example_duration):
                    self.stop_example_recording()
            
            # Clean up
            cv2.destroyAllWindows()
            session_dir = self.end_training_session()
            return session_dir
            
        except Exception as e:
            logger.error(f"Error during training session: {str(e)}")
            self.end_training_session()
            return None
        finally:
            self.stop_camera()
