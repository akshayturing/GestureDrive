# core/mediapipe_handler.py
import cv2
import mediapipe as mp
import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any, NamedTuple
import dataclasses
from enum import Enum
import logging

class HandSide(Enum):
    """Standardized enum for hand side identification."""
    UNKNOWN = "unknown"
    LEFT = "left"
    RIGHT = "right"

@dataclasses.dataclass
class HandLandmark:
    """Standardized container for single landmark data."""
    x: float           # Normalized x coordinate (0.0 - 1.0)
    y: float           # Normalized y coordinate (0.0 - 1.0)
    z: float           # Normalized z coordinate (relative to wrist)
    visibility: float  # Confidence value (0.0 - 1.0)

@dataclasses.dataclass
class ProcessedHand:
    """Standardized hand data container."""
    landmarks: List[HandLandmark]  # List of 21 landmarks
    hand_side: HandSide            # Left or right hand
    confidence: float              # Detection confidence
    id: int                        # Tracking ID (consistent across frames if available)
    
    # Computed properties
    bounding_box: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    rotation: Optional[float] = None                          # Rotation in degrees
    palm_center: Optional[Tuple[float, float, float]] = None  # (x, y, z)

class MediaPipeHandler:
    """
    Centralized MediaPipe hand tracking handler.
    
    Provides unified interface for hand tracking and landmark extraction
    to be used consistently across all system components.
    """
    
    # MediaPipe landmark indices for reference
    LANDMARK_INDICES = {
        "WRIST": 0,
        "THUMB_CMC": 1,
        "THUMB_MCP": 2,
        "THUMB_IP": 3,
        "THUMB_TIP": 4,
        "INDEX_MCP": 5,
        "INDEX_PIP": 6,
        "INDEX_DIP": 7,
        "INDEX_TIP": 8,
        "MIDDLE_MCP": 9,
        "MIDDLE_PIP": 10,
        "MIDDLE_DIP": 11,
        "MIDDLE_TIP": 12,
        "RING_MCP": 13,
        "RING_PIP": 14,
        "RING_DIP": 15,
        "RING_TIP": 16,
        "PINKY_MCP": 17,
        "PINKY_PIP": 18,
        "PINKY_DIP": 19,
        "PINKY_TIP": 20
    }
    
    # Finger connections for visualization
    CONNECTIONS = [
        # Thumb
        (0, 1), (1, 2), (2, 3), (3, 4),
        # Index finger
        (0, 5), (5, 6), (6, 7), (7, 8),
        # Middle finger
        (0, 9), (9, 10), (10, 11), (11, 12),
        # Ring finger
        (0, 13), (13, 14), (14, 15), (15, 16),
        # Pinky
        (0, 17), (17, 18), (18, 19), (19, 20),
        # Palm
        (0, 5), (5, 9), (9, 13), (13, 17)
    ]
    
    def __init__(self, 
                 static_image_mode: bool = False,
                 max_num_hands: int = 2,
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5,
                 model_complexity: int = 1):
        """
        Initialize MediaPipe hand tracking with standard parameters.
        
        Args:
            static_image_mode: Whether to treat input as static images (vs video)
            max_num_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for hand detection
            min_tracking_confidence: Minimum confidence for hand tracking
            model_complexity: Model complexity (0, 1, or 2); higher is more accurate but slower
        """
        self.logger = logging.getLogger("MediaPipeHandler")
        
        # Store configuration
        self.config = {
            'static_image_mode': static_image_mode,
            'max_num_hands': max_num_hands,
            'min_detection_confidence': min_detection_confidence,
            'min_tracking_confidence': min_tracking_confidence,
            'model_complexity': model_complexity
        }
        
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity
        )
        
        # Initialize drawing utilities
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Performance tracking
        self.last_process_time = 0
        self.process_times = []  # For rolling average
        
        self.logger.info(f"MediaPipe handler initialized with complexity={model_complexity}, "
                        f"max_hands={max_num_hands}")
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Process a video frame to extract hand landmarks.
        
        Args:
            frame: OpenCV BGR image
            
        Returns:
            Dictionary with processing results including hands and performance metrics
        """
        if frame is None:
            self.logger.warning("Received empty frame for processing")
            return {'hands': [], 'processing_time_ms': 0}
        
        # Start timing
        start_time = time.time()
        
        # Convert to RGB (MediaPipe requirement)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame
        results = self.mp_hands.process(rgb_frame)
        
        # Extract and standardize hand data
        processed_hands = self._extract_hand_data(results, frame.shape)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        self.last_process_time = processing_time_ms
        
        # Keep last 30 processing times for statistics
        self.process_times.append(processing_time_ms)
        if len(self.process_times) > 30:
            self.process_times.pop(0)
        
        # Return standardized results
        return {
            'hands': processed_hands,
            'processing_time_ms': processing_time_ms,
            'avg_processing_time_ms': sum(self.process_times) / len(self.process_times) if self.process_times else 0,
            'frame_dimensions': (frame.shape[1], frame.shape[0]),  # width, height
            'timestamp': time.time()
        }
    
    def _extract_hand_data(self, results, frame_shape) -> List[ProcessedHand]:
        """
        Extract standardized hand data from MediaPipe results.
        
        Args:
            results: MediaPipe hand processing results
            frame_shape: Original frame dimensions (height, width, channels)
            
        Returns:
            List of ProcessedHand objects
        """
        processed_hands = []
        
        # Check if hand landmarks were detected
        if not results.multi_hand_landmarks:
            return processed_hands
        
        # Extract data for each detected hand
        for idx, (hand_landmarks, handedness) in enumerate(zip(
                results.multi_hand_landmarks or [],
                results.multi_handedness or [])):
            
            # Determine hand side (left/right)
            hand_side = HandSide.UNKNOWN
            confidence = 0.0
            
            if handedness:
                # Extract handedness classification
                classification = handedness.classification[0]
                label = classification.label
                confidence = classification.score
                
                if label.lower() == "left":
                    hand_side = HandSide.LEFT
                elif label.lower() == "right":
                    hand_side = HandSide.RIGHT
            
            # Convert landmarks to our standardized format
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append(HandLandmark(
                    x=lm.x,
                    y=lm.y,
                    z=lm.z,
                    visibility=getattr(lm, 'visibility', 1.0)  # Default to 1.0 if not available
                ))
            
            # Calculate bounding box
            frame_width, frame_height = frame_shape[1], frame_shape[0]
            x_coords = [lm.x for lm in landmarks]
            y_coords = [lm.y for lm in landmarks]
            
            x_min = max(0, int(min(x_coords) * frame_width))
            y_min = max(0, int(min(y_coords) * frame_height))
            x_max = min(frame_width, int(max(x_coords) * frame_width))
            y_max = min(frame_height, int(max(y_coords) * frame_height))
            
            bounding_box = (x_min, y_min, x_max - x_min, y_max - y_min)
            
            # Calculate palm center
            wrist = landmarks[self.LANDMARK_INDICES["WRIST"]]
            middle_mcp = landmarks[self.LANDMARK_INDICES["MIDDLE_MCP"]]
            palm_center = (
                (wrist.x + middle_mcp.x) / 2,
                (wrist.y + middle_mcp.y) / 2,
                (wrist.z + middle_mcp.z) / 2
            )
            
            # Calculate hand rotation (angle between wrist-middle_mcp line and vertical)
            dx = middle_mcp.x - wrist.x
            dy = middle_mcp.y - wrist.y
            rotation = np.degrees(np.arctan2(dx, -dy))  # Negative dy for proper orientation
            
            # Create standardized hand object
            hand = ProcessedHand(
                landmarks=landmarks,
                hand_side=hand_side,
                confidence=confidence,
                id=idx,
                bounding_box=bounding_box,
                rotation=rotation,
                palm_center=palm_center
            )
            
            processed_hands.append(hand)
        
        return processed_hands
    
    def draw_landmarks(self, frame: np.ndarray, hand: ProcessedHand,
                      landmark_color=(0, 255, 0), connection_color=(0, 0, 255),
                      thickness=2) -> np.ndarray:
        """
        Draw hand landmarks on a frame.
        
        Args:
            frame: OpenCV image to draw on
            hand: ProcessedHand object with landmark data
            landmark_color: RGB color for landmarks
            connection_color: RGB color for connections
            thickness: Line thickness
            
        Returns:
            Frame with landmarks drawn
        """
        if frame is None or hand is None:
            return frame
            
        height, width = frame.shape[:2]
        
        # Draw connections
        for start_idx, end_idx in self.CONNECTIONS:
            start_point = hand.landmarks[start_idx]
            end_point = hand.landmarks[end_idx]
            
            # Convert normalized coordinates to pixel coordinates
            start_xy = (int(start_point.x * width), int(start_point.y * height))
            end_xy = (int(end_point.x * width), int(end_point.y * height))
            
            # Draw line
            cv2.line(frame, start_xy, end_xy, connection_color, thickness)
        
        # Draw landmarks
        for idx, landmark in enumerate(hand.landmarks):
            # Convert to pixel coordinates
            x, y = int(landmark.x * width), int(landmark.y * height)
            
            # Draw circle
            cv2.circle(frame, (x, y), thickness + 2, landmark_color, -1)
            
            # Optionally add landmark indices for debugging
            # cv2.putText(frame, str(idx), (x+5, y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Draw hand side label
        if hand.bounding_box:
            x, y, w, h = hand.bounding_box
            label = f"{hand.hand_side.value} ({hand.confidence:.2f})"
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
    
    def draw_all_hands(self, frame: np.ndarray, hands: List[ProcessedHand]) -> np.ndarray:
        """
        Draw all hands on a frame.
        
        Args:
            frame: OpenCV image
            hands: List of ProcessedHand objects
            
        Returns:
            Frame with all hands drawn
        """
        if frame is None:
            return frame
            
        result_frame = frame.copy()
        
        # Colors for different hands
        colors = [
            ((0, 255, 0), (0, 200, 0)),  # Green landmarks, dark green connections
            ((0, 0, 255), (0, 0, 200)),  # Blue landmarks, dark blue connections
            ((255, 0, 0), (200, 0, 0)),  # Red landmarks, dark red connections
            ((255, 0, 255), (200, 0, 200))  # Purple landmarks, dark purple connections
        ]
        
        for i, hand in enumerate(hands):
            # Use modulo to cycle through colors if more hands than colors
            color_idx = i % len(colors)
            landmark_color, connection_color = colors[color_idx]
            
            result_frame = self.draw_landmarks(
                result_frame, hand, landmark_color, connection_color
            )
        
        return result_frame
    
    def serialize_hand(self, hand: ProcessedHand) -> Dict[str, Any]:
        """
        Serialize a ProcessedHand to a dictionary for storage or transmission.
        
        Args:
            hand: ProcessedHand object
            
        Returns:
            Dictionary representation
        """
        # Convert landmarks to list of dicts
        landmarks_data = [
            {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
            for lm in hand.landmarks
        ]
        
        return {
            "landmarks": landmarks_data,
            "hand_side": hand.hand_side.value,
            "confidence": hand.confidence,
            "id": hand.id,
            "bounding_box": hand.bounding_box,
            "rotation": hand.rotation,
            "palm_center": hand.palm_center
        }
    
    @staticmethod
    def deserialize_hand(data: Dict[str, Any]) -> ProcessedHand:
        """
        Deserialize a dictionary to a ProcessedHand object.
        
        Args:
            data: Dictionary with hand data
            
        Returns:
            ProcessedHand object
        """
        # Convert landmark dictionaries to HandLandmark objects
        landmarks = [
            HandLandmark(
                x=lm["x"],
                y=lm["y"],
                z=lm["z"],
                visibility=lm.get("visibility", 1.0)
            )
            for lm in data["landmarks"]
        ]
        
        # Determine hand side
        try:
            hand_side = HandSide(data["hand_side"])
        except ValueError:
            hand_side = HandSide.UNKNOWN
        
        return ProcessedHand(
            landmarks=landmarks,
            hand_side=hand_side,
            confidence=data["confidence"],
            id=data["id"],
            bounding_box=data.get("bounding_box"),
            rotation=data.get("rotation"),
            palm_center=data.get("palm_center")
        )
    
    def release(self):
        """Release MediaPipe resources."""
        if hasattr(self, 'mp_hands'):
            self.mp_hands.close()
            self.logger.info("MediaPipe resources released")