# hand_motion_player.py
import cv2
import numpy as np
import mediapipe as mp
import time
import json
import os
from typing import Dict, List, Optional, Tuple, Union
import logging
from hand_motion_visualizer import HandMotionVisualizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HandMotionPlayer:
    """
    Plays back recorded hand motion sequences, with options for
    speed control, looping, and visualization.
    """
    
    def __init__(self, visualizer: Optional[HandMotionVisualizer] = None):
        """
        Initialize the HandMotionPlayer.
        
        Args:
            visualizer: Optional HandMotionVisualizer to use for rendering
        """
        self.visualizer = visualizer or HandMotionVisualizer()
        self.current_recording = None
        self.is_playing = False
        self.loop = False
        self.playback_speed = 1.0
        self.current_frame_index = 0
        
        logger.info("HandMotionPlayer initialized")
    
    def load_recording(self, filepath: str) -> bool:
        """
        Load a hand motion recording from a file.
        
        Args:
            filepath: Path to the recording JSON file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                self.current_recording = json.load(f)
                
            self.current_frame_index = 0
            logger.info(f"Loaded recording from {filepath} with {len(self.current_recording.get('frames', []))} frames")
            return True
            
        except Exception as e:
            logger.error(f"Error loading recording: {str(e)}")
            return False
    
    def set_recording(self, recording: Dict) -> bool:
        """
        Set the current recording directly from a dictionary.
        
        Args:
            recording: Recording data dictionary
            
        Returns:
            True if valid recording, False otherwise
        """
        if not recording or "frames" not in recording or not recording["frames"]:
            logger.error("Invalid recording data")
            return False
            
        self.current_recording = recording
        self.current_frame_index = 0
        logger.info(f"Set recording with {len(recording.get('frames', []))} frames")
        return True
    
    def play(self, loop: bool = False, playback_speed: float = 1.0) -> bool:
        """
        Start playback of the current recording.
        
        Args:
            loop: Whether to loop playback when reaching the end
            playback_speed: Playback speed multiplier (1.0 = normal speed)
            
        Returns:
            True if playback started successfully, False otherwise
        """
        if not self.current_recording:
            logger.error("No recording loaded")
            return False
            
        if self.is_playing:
            logger.warning("Already playing")
            return False
            
        self.is_playing = True
        self.loop = loop
        self.playback_speed = max(0.1, playback_speed)  # Ensure reasonable speed
        
        logger.info(f"Started playback (speed: {playback_speed}x, loop: {loop})")
        return True
    
    def stop(self):
        """Stop playback"""
        self.is_playing = False
        logger.info("Stopped playback")
    
    def pause(self):
        """Pause playback"""
        self.is_playing = False
        logger.info("Paused playback")
    
    def resume(self):
        """Resume paused playback"""
        if not self.current_recording:
            logger.error("No recording loaded")
            return False
            
        self.is_playing = True
        logger.info("Resumed playback")
        return True
    
    def seek(self, frame_index: int) -> bool:
        """
        Seek to a specific frame.
        
        Args:
            frame_index: Frame index to seek to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_recording:
            logger.error("No recording loaded")
            return False
            
        frames = self.current_recording.get("frames", [])
        if not frames:
            logger.error("Recording has no frames")
            return False
            
        # Clamp frame index to valid range
        frame_index = max(0, min(frame_index, len(frames) - 1))
        self.current_frame_index = frame_index
        
        logger.info(f"Seeked to frame {frame_index}")
        return True
    
    def seek_percent(self, percent: float) -> bool:
        """
        Seek to a position by percentage of total duration.
        
        Args:
            percent: Percentage position (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_recording:
            logger.error("No recording loaded")
            return False
            
        frames = self.current_recording.get("frames", [])
        if not frames:
            logger.error("Recording has no frames")
            return False
            
        # Calculate frame index from percentage
        percent = max(0, min(100, percent))
        frame_index = int((percent / 100) * (len(frames) - 1))
        
        return self.seek(frame_index)
    
    def get_current_frame(self) -> Optional[Dict]:
        """
        Get the current frame data.
        
        Returns:
            Current frame data or None if no recording loaded
        """
        if not self.current_recording:
            return None
            
        frames = self.current_recording.get("frames", [])
        if not frames or self.current_frame_index >= len(frames):
            return None
            
        return frames[self.current_frame_index]
    
    def get_recording_metadata(self) -> Dict:
        """
        Get metadata about the current recording.
        
        Returns:
            Dictionary with recording metadata
        """
        if not self.current_recording:
            return {}
            
        metadata = self.current_recording.get("metadata", {})
        frames = self.current_recording.get("frames", [])
        
        return {
            **metadata,
            "frame_count": len(frames),
            "current_frame": self.current_frame_index,
            "progress_percent": (self.current_frame_index / max(1, len(frames) - 1)) * 100 if frames else 0
        }
    
    def step_forward(self, steps: int = 1) -> bool:
        """
        Step forward by the specified number of frames.
        
        Args:
            steps: Number of frames to advance
            
        Returns:
            True if successful, False otherwise
        """
        if not self.current_recording:
            logger.error("No recording loaded")
            return False
            
        frames = self.current_recording.get("frames", [])
        if not frames:
            logger.error("Recording has no frames")
            return False
            
        new_index = self.current_frame_index + steps
        
        # Handle looping if enabled
        if self.loop and new_index >= len(frames):
            new_index = new_index % len(frames)
        else:
            # Clamp to valid range
            new_index = max(0, min(new_index, len(frames) - 1))
            
            # Check if we reached the end
            if new_index == len(frames) - 1 and self.current_frame_index != new_index:
                logger.info("Reached end of recording")
        
        self.current_frame_index = new_index
        return True
    
    def step_backward(self, steps: int = 1) -> bool:
        """
        Step backward by the specified number of frames.
        
        Args:
            steps: Number of frames to go back
            
        Returns:
            True if successful, False otherwise
        """
        return self.step_forward(-steps)
    
    def play_interactive(self, window_name: str = "Hand Motion Player",
                       display_size: Tuple[int, int] = (640, 480)) -> None:
        """
        Play the recording in an interactive window with playback controls.
        
        Args:
            window_name: Name for the display window
            display_size: Size of the display window
        """
        if not self.current_recording:
            logger.error("No recording loaded")
            return
            
        frames = self.current_recording.get("frames", [])
        if not frames:
            logger.error("Recording has no frames")
            return
            
        # Create window
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, display_size[0], display_size[1])
        
        # Create trackbar for frame seeking
        def on_trackbar_change(value):
            self.seek(value)
            
        cv2.createTrackbar("Frame", window_name, 0, len(frames) - 1, on_trackbar_change)
        
        # Start playback
        self.play(loop=self.loop, playback_speed=self.playback_speed)
        
        # Variables to manage timing
        target_frame_time = 1.0 / 30.0  # Target 30 FPS
        last_frame_time = time.time()
        
        # Playback loop
        while True:
            # Capture current time
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            # Calculate if we should update frame based on playback speed
            should_update = self.is_playing and elapsed >= (target_frame_time / self.playback_speed)
            
            if should_update:
                # Move to next frame
                reached_end = not self.step_forward()
                if reached_end and not self.loop:
                    self.pause()
                    
                # Update last frame time
                last_frame_time = current_time
                
                # Update trackbar position
                cv2.setTrackbarPos("Frame", window_name, self.current_frame_index)
            
            # Get the current frame visualization
            frame = self.visualizer.visualize_recording_frame(
                self.current_recording, self.current_frame_index, display_size
            )
            
            # Add playback status to the visualization
            status_text = "▶" if self.is_playing else "⏸"
            status_text += f" {self.playback_speed:.1f}x"
            if self.loop:
                status_text += " 🔁"
                
            cv2.putText(frame, status_text, (10, display_size[1] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                
            # Display current progress
            metadata = self.get_recording_metadata()
            progress = metadata.get("progress_percent", 0)
            cv2.putText(frame, f"{progress:.1f}%", (display_size[0] - 100, display_size[1] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Show frame
            cv2.imshow(window_name, frame)
            
            # Process key events
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == ord(' '):  # Space bar
                if self.is_playing:
                    self.pause()
                else:
                    self.resume()
            elif key == ord('r'):  # 'r' key
                self.loop = not self.loop
            elif key == ord('+') or key == ord('='):  # '+' key
                self.playback_speed = min(4.0, self.playback_speed + 0.1)
            elif key == ord('-'):  # '-' key
                self.playback_speed = max(0.1, self.playback_speed - 0.1)
            elif key == ord('[') or key == ord(','):  # Previous frame
                self.pause()
                self.step_backward()
                cv2.setTrackbarPos("Frame", window_name, self.current_frame_index)
            elif key == ord(']') or key == ord('.'):  # Next frame
                self.pause()
                self.step_forward()
                cv2.setTrackbarPos("Frame", window_name, self.current_frame_index)
            elif key == ord('0'):  # Reset speed
                self.playback_speed = 1.0
            elif key == ord('h'):  # Generate heatmap
                heatmap = self.visualizer.generate_motion_heatmap(self.current_recording, display_size)
                cv2.imshow("Motion Heatmap", heatmap)
        
        # Clean up
        cv2.destroyAllWindows()
        self.stop()
