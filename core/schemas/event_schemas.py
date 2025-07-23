from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict, Literal
from dataclasses import dataclass
import time
import numpy as np

class HandLandmark(TypedDict):
    x: float  # Normalized x coordinate (0.0 - 1.0)
    y: float  # Normalized y coordinate (0.0 - 1.0)
    z: float  # Normalized z coordinate
    visibility: float  # Landmark visibility score (0.0 - 1.0)

class HandData(TypedDict):
    landmarks: List[HandLandmark]  # 21 hand landmarks
    handedness: Literal["Left", "Right"]  # Which hand
    score: float  # Detection confidence (0.0 - 1.0)

class GestureType(Enum):
    UNKNOWN = "unknown"
    FIST = "fist"
    OPEN_PALM = "open_palm"
    POINT_UP = "point_up"
    POINT_DOWN = "point_down"
    POINT_LEFT = "point_left"
    POINT_RIGHT = "point_right"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    VICTORY = "victory"
    OK = "ok"

class MotionType(Enum):
    STATIONARY = "stationary"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    CIRCLE_CW = "circle_cw"
    CIRCLE_CCW = "circle_ccw"
    PINCH = "pinch"
    SPREAD = "spread"
    INSUFFICIENT_DATA = "insufficient_data"

class ActionContext(Enum):
    DEFAULT = "default"
    FILE_BROWSER = "file_browser"
    MEDIA_PLAYER = "media_player"
    SETTINGS = "settings"
    CALIBRATION = "calibration"

@dataclass
class FrameData:
    """Camera frame data schema."""
    frame_id: int  # Unique frame identifier
    timestamp: float  # Capture time (seconds since epoch)
    image: np.ndarray  # OpenCV image data
    width: int  # Frame width in pixels
    height: int  # Frame height in pixels 
    format: str = "BGR"  # Image format (BGR, RGB, etc)
    
    def validate(self) -> bool:
        """Validate frame data."""
        if self.image is None or not isinstance(self.image, np.ndarray):
            return False
        if len(self.image.shape) != 3:
            return False
        if self.image.shape[0] != self.height or self.image.shape[1] != self.width:
            return False
        return True

@dataclass
class GestureData:
    """Detected gesture event data schema."""
    gesture: GestureType  # Type of gesture detected
    confidence: float  # Confidence score (0.0 - 1.0)
    hand_data: Optional[HandData]  # Hand landmark data (if available)
    frame_id: int  # Source frame ID
    timestamp: float  # Detection time (seconds since epoch)
    
    def validate(self) -> bool:
        """Validate gesture data."""
        if not isinstance(self.gesture, GestureType):
            return False
        if not 0.0 <= self.confidence <= 1.0:
            return False
        return True

@dataclass
class MotionData:
    """Detected motion event data schema."""
    motion: MotionType  # Type of motion detected
    velocity: Dict[str, float]  # Velocity components (vx, vy, magnitude)
    duration: float  # Motion duration in seconds
    frame_id: int  # Source frame ID  
    timestamp: float  # Detection time (seconds since epoch)
    
    def validate(self) -> bool:
        """Validate motion data."""
        if not isinstance(self.motion, MotionType):
            return False
        required_keys = {"vx", "vy", "magnitude"}
        if not all(k in self.velocity for k in required_keys):
            return False
        return True

@dataclass
class ActionTrigger:
    """Action trigger event data schema."""
    action_id: str  # Unique action identifier (e.g., "navigate.move_forward")
    context: ActionContext  # Current UI context
    source: Literal["gesture", "motion", "manual", "system"]  # Trigger source
    source_data: Dict[str, Any]  # Original trigger data
    timestamp: float  # Trigger time (seconds since epoch)
    
    def validate(self) -> bool:
        """Validate action trigger data."""
        if not isinstance(self.context, ActionContext):
            return False
        if not self.action_id or not isinstance(self.action_id, str):
            return False
        return True

@dataclass
class ActionResult:
    """Action execution result schema."""
    action_id: str  # Executed action identifier
    success: bool  # Whether action succeeded
    result: Optional[Dict[str, Any]]  # Action-specific result data
    error: Optional[str]  # Error message if action failed
    timestamp: float  # Execution time (seconds since epoch)
    duration: float  # Execution duration in seconds