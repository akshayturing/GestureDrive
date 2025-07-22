# hand_motion_visualizer.py
import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Optional, Tuple, Union
import logging
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HandMotionVisualizer:
    """
    Visualizes hand motion data with various rendering options and animations.
    """
    
    def __init__(self):
        """Initialize the HandMotionVisualizer"""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Define custom landmark styles
        self.custom_landmark_style = self.mp_drawing_styles.get_default_hand_landmarks_style()
        self.custom_connection_style = self.mp_drawing_styles.get_default_hand_connections_style()
        
        # Motion trail parameters
        self.trail_length = 30  # Number of frames to keep in the trail
        self.trail_fade = 0.8   # How quickly the trail fades out (0-1)
        
        # Animation parameters
        self.anim = None        # Store the animation object
        self.fig = None         # Store the figure for animations
        
        logger.info("HandMotionVisualizer initialized")
    
    def draw_landmarks_on_image(self, image: np.ndarray, hand_landmarks: Dict, 
                              draw_connections: bool = True, 
                              draw_trail: bool = False,
                              previous_landmarks: List = None) -> np.ndarray:
        """
        Draw hand landmarks and connections on an image.
        
        Args:
            image: Image to draw on
            hand_landmarks: MediaPipe hand landmarks
            draw_connections: Whether to draw connections between landmarks
            draw_trail: Whether to draw motion trails
            previous_landmarks: List of previous landmark positions for trails
            
        Returns:
            Image with landmarks drawn
        """
        # Create a copy of the image to draw on
        annotated_image = image.copy()
        
        # Convert landmarks to the MediaPipe format if needed
        if isinstance(hand_landmarks, dict):
            # Convert our dictionary format to MediaPipe landmark format
            mp_landmarks = self._dict_to_mp_landmarks(hand_landmarks)
        else:
            # Already in MediaPipe format
            mp_landmarks = hand_landmarks
        
        # Draw the landmarks and connections
        if mp_landmarks:
            if draw_connections:
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    mp_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.custom_landmark_style,
                    self.custom_connection_style
                )
            else:
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    mp_landmarks,
                    None,
                    self.custom_landmark_style
                )
                
            # Draw motion trails if requested and we have previous landmarks
            if draw_trail and previous_landmarks and len(previous_landmarks) > 0:
                self._draw_motion_trails(annotated_image, mp_landmarks, previous_landmarks)
        
        return annotated_image
    
    def _dict_to_mp_landmarks(self, hand_dict: Dict) -> Optional[mp.solutions.hands.HandLandmark]:
        """Convert our dictionary landmark format to MediaPipe format"""
        if not hand_dict or "landmarks" not in hand_dict or not hand_dict["landmarks"]:
            return None
            
        # Create a mock landmark object
        class MockLandmark:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        class MockHandLandmarks:
            def __init__(self, landmarks):
                self.landmark = landmarks
        
        # Convert our landmarks to the format MediaPipe expects
        mp_landmarks = []
        for lm in hand_dict["landmarks"]:
            if len(lm) >= 3:
                mp_landmarks.append(MockLandmark(lm[0], lm[1], lm[2]))
            elif len(lm) == 2:
                mp_landmarks.append(MockLandmark(lm[0], lm[1], 0.0))
        
        return MockHandLandmarks(mp_landmarks)
    
    def _draw_motion_trails(self, image: np.ndarray, current_landmarks, previous_landmarks: List):
        """Draw motion trails for key landmarks"""
        image_height, image_width, _ = image.shape
        
        # Define key landmarks to track (wrist, thumb tip, finger tips)
        key_indices = [0, 4, 8, 12, 16, 20]
        
        for idx in key_indices:
            # Get current landmark position
            current_lm = current_landmarks.landmark[idx]
            current_pos = (int(current_lm.x * image_width), int(current_lm.y * image_height))
            
            # Draw trail from previous positions
            positions = []
            for i, prev_landmarks in enumerate(previous_landmarks):
                if not prev_landmarks or not hasattr(prev_landmarks, 'landmark'):
                    continue
                    
                if idx < len(prev_landmarks.landmark):
                    prev_lm = prev_landmarks.landmark[idx]
                    prev_pos = (int(prev_lm.x * image_width), int(prev_lm.y * image_height))
                    positions.append((i, prev_pos))
            
            # Draw lines with decreasing opacity
            if positions:
                for i in range(len(positions) - 1):
                    # Calculate alpha based on position in the trail
                    alpha = 1.0 - (i / len(positions)) * self.trail_fade
                    
                    # Determine color (using landmark color * alpha)
                    color = self.custom_landmark_style[idx].color
                    adjusted_color = (
                        int(color[0] * alpha),
                        int(color[1] * alpha),
                        int(color[2] * alpha)
                    )
                    
                    # Draw the trail segment
                    cv2.line(image, positions[i][1], positions[i+1][1], adjusted_color, 2)
    
    def visualize_recording_frame(self, recording: Dict, frame_idx: int = 0, 
                                display_size: Tuple[int, int] = (640, 480)) -> np.ndarray:
        """
        Visualize a specific frame from a recording.
        
        Args:
            recording: Recording dictionary
            frame_idx: Index of the frame to visualize
            display_size: Size of the output visualization
            
        Returns:
            Image with visualization
        """
        if not recording or "frames" not in recording or not recording["frames"]:
            logger.error("Invalid recording data")
            return np.zeros((*display_size, 3), dtype=np.uint8)
        
        # Get recording metadata
        metadata = recording.get("metadata", {})
        frames = recording.get("frames", [])
        
        if frame_idx >= len(frames):
            logger.error(f"Frame index {frame_idx} out of bounds (max: {len(frames) - 1})")
            return np.zeros((*display_size, 3), dtype=np.uint8)
        
        # Get the requested frame
        frame_data = frames[frame_idx]
        
        # Create a blank canvas
        width, height = display_size
        image = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Draw frame info
        cv2.putText(image, f"Frame: {frame_idx+1}/{len(frames)}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        timestamp = frame_data.get("timestamp", 0)
        if metadata.get("timestamp"):
            # Calculate relative time if we have a recording start time
            start_time = metadata.get("timestamp", 0)
            relative_time = timestamp - float(start_time) if isinstance(start_time, (int, float)) else 0
            cv2.putText(image, f"Time: {relative_time:.2f}s", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # Draw label if present
        if metadata.get("label"):
            cv2.putText(image, f"Label: {metadata['label']}", (width - 200, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        # Draw hand landmarks for each hand in the frame
        hands = frame_data.get("hands", [])
        for hand_idx, hand in enumerate(hands):
            # Get previous frames for motion trails
            previous_hands = []
            for i in range(max(0, frame_idx - self.trail_length), frame_idx):
                prev_frame = frames[i]
                if hand_idx < len(prev_frame.get("hands", [])):
                    prev_hand = prev_frame["hands"][hand_idx]
                    prev_mp_hand = self._dict_to_mp_landmarks(prev_hand)
                    if prev_mp_hand:
                        previous_hands.append(prev_mp_hand)
            
            # Draw the landmarks with trails
            image = self.draw_landmarks_on_image(
                image, 
                hand, 
                draw_connections=True, 
                draw_trail=True,
                previous_landmarks=previous_hands
            )
        
        return image
    
    def create_recording_animation(self, recording: Dict, 
                                 display_size: Tuple[int, int] = (640, 480),
                                 fps: int = 30) -> Optional[FuncAnimation]:
        """
        Create an animation of a hand motion recording.
        
        Args:
            recording: Recording dictionary
            display_size: Size of the output visualization
            fps: Frames per second for the animation
            
        Returns:
            Matplotlib animation object
        """
        if not recording or "frames" not in recording or not recording["frames"]:
            logger.error("Invalid recording data")
            return None
        
        frames = recording.get("frames", [])
        if not frames:
            logger.error("Recording has no frames")
            return None
            
        # Create figure and axes
        self.fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_axis_off()
        
        # Initialize with the first frame
        first_frame = self.visualize_recording_frame(recording, 0, display_size)
        img_obj = ax.imshow(cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB))
        
        # Update function for animation
        def update(frame_idx):
            frame = self.visualize_recording_frame(recording, frame_idx, display_size)
            img_obj.set_array(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            return [img_obj]
        
        # Create animation
        self.anim = FuncAnimation(
            self.fig, update, frames=len(frames), 
            interval=1000/fps, blit=True
        )
        
        plt.tight_layout()
        return self.anim
    
    def save_animation(self, filename: str, fps: int = 30, dpi: int = 100) -> bool:
        """
        Save the current animation to a file.
        
        Args:
            filename: Output filename (should end with .mp4, .gif, etc.)
            fps: Frames per second
            dpi: Resolution (dots per inch)
            
        Returns:
            True if successful, False otherwise
        """
        if self.anim is None:
            logger.error("No animation to save. Create one first with create_recording_animation().")
            return False
        
        try:
            # Configure writer based on file extension
            if filename.endswith('.gif'):
                writer = 'pillow'
            elif filename.endswith('.mp4'):
                writer = 'ffmpeg'
            else:
                writer = None
                
            self.anim.save(filename, fps=fps, dpi=dpi, writer=writer)
            logger.info(f"Animation saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving animation: {str(e)}")
            return False
    
    def create_3d_trajectory_animation(self, recording: Dict, landmark_index: int = 8,
                                     hand_index: int = 0) -> Optional[FuncAnimation]:
        """
        Create a 3D animation of a hand landmark's trajectory.
        
        Args:
            recording: Recording dictionary
            landmark_index: Index of the landmark to visualize
            hand_index: Which hand to use if multiple are present
            
        Returns:
            Matplotlib animation object
        """
        if not recording or "frames" not in recording or not recording["frames"]:
            logger.error("Invalid recording data")
            return None
            
        # Extract trajectory
        trajectory = []
        for frame in recording.get("frames", []):
            hands = frame.get("hands", [])
            if hand_index < len(hands):
                hand = hands[hand_index]
                landmarks = hand.get("landmarks", [])
                
                if landmark_index < len(landmarks):
                    trajectory.append(landmarks[landmark_index])
        
        if not trajectory:
            logger.error(f"No trajectory data for landmark {landmark_index}")
            return None
            
        # Convert to numpy array
        trajectory = np.array(trajectory)
        
        # Create figure and 3D axes
        self.fig = plt.figure(figsize=(10, 8))
        ax = self.fig.add_subplot(111, projection='3d')
        
        # Determine axis limits
        x_min, x_max = np.min(trajectory[:, 0]), np.max(trajectory[:, 0])
        y_min, y_max = np.min(trajectory[:, 1]), np.max(trajectory[:, 1])
        z_min, z_max = np.min(trajectory[:, 2]), np.max(trajectory[:, 2])
        
        # Add padding to limits
        padding = 0.1
        x_range = x_max - x_min
        y_range = y_max - y_min
        z_range = z_max - z_min
        x_min -= padding * x_range
        x_max += padding * x_range
        y_min -= padding * y_range
        y_max += padding * y_range
        z_min -= padding * z_range
        z_max += padding * z_range
        
        # Set limits
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_zlim(z_min, z_max)
        
        # Set labels
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(f'3D Trajectory of Landmark {landmark_index}')
        
        # Initialize empty plot objects
        line, = ax.plot([], [], [], 'b-', label='Trajectory')
        point, = ax.plot([], [], [], 'ro', markersize=8, label='Current Position')
        
        # Add legend
        ax.legend()
        
        # Update function for animation
        def update(frame_idx):
            # Update line data (show trajectory up to current frame)
            line.set_data(trajectory[:frame_idx+1, 0], trajectory[:frame_idx+1, 1])
            line.set_3d_properties(trajectory[:frame_idx+1, 2])
            
            # Update point data (current position)
            point.set_data([trajectory[frame_idx, 0]], [trajectory[frame_idx, 1]])
            point.set_3d_properties([trajectory[frame_idx, 2]])
            
            return line, point
        
        # Create animation
        self.anim = FuncAnimation(
            self.fig, update, frames=len(trajectory),
            interval=1000/30, blit=True
        )
        
        plt.tight_layout()
        return self.anim
    
    def generate_motion_heatmap(self, recording: Dict, resolution: Tuple[int, int] = (640, 480),
                              alpha: float = 0.7) -> np.ndarray:
        """
        Generate a visual heatmap of hand motion density.
        
        Args:
            recording: Recording dictionary
            resolution: Resolution of the output image
            alpha: Transparency of the heatmap overlay
            
        Returns:
            Heatmap image
        """
        # Create a blank canvas
        heatmap = np.zeros((*resolution, 3), dtype=np.uint8)
        
        # Extract all landmark positions
        positions = []
        
        for frame in recording.get("frames", []):
            hands = frame.get("hands", [])
            for hand in hands:
                landmarks = hand.get("landmarks", [])
                for lm in landmarks:
                    # Convert normalized coordinates to pixel coordinates
                    x, y = int(lm[0] * resolution[0]), int(lm[1] * resolution[1])
                    
                    # Ensure coordinates are within bounds
                    if 0 <= x < resolution[0] and 0 <= y < resolution[1]:
                        positions.append((x, y))
        
        # If no positions, return the empty canvas
        if not positions:
            return heatmap
        
        # Create a simple heatmap by incrementing pixels where landmarks were detected
        for x, y in positions:
            # Increase the value at this position
            # We use a small area around each point for better visibility
            cv2.circle(heatmap, (x, y), 5, (0, 0, 255), -1)
        
        # Apply Gaussian blur to smooth the heatmap
        heatmap = cv2.GaussianBlur(heatmap, (15, 15), 0)
        
        # Normalize the heatmap for better visualization
        heatmap_max = heatmap.max()
        if heatmap_max > 0:
            heatmap = (heatmap / heatmap_max * 255).astype(np.uint8)
        
        # Apply a colormap for better visualization
        heatmap = cv2.applyColorMap(
            cv2.cvtColor(heatmap, cv2.COLOR_BGR2GRAY),
            cv2.COLORMAP_JET
        )
        
        # Create a background image
        background = np.ones((*resolution, 3), dtype=np.uint8) * 255
        
        # Overlay heatmap on background
        result = cv2.addWeighted(background, 1 - alpha, heatmap, alpha, 0)
        
        return result
