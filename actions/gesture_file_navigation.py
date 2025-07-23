# gesture_file_navigation.py

import cv2
import time
import os
import pathlib
import numpy as np
import argparse
import threading
from typing import Dict, Any

from core.camera import Camera
from actions.dynamic_gesture_navigator import DynamicGestureNavigator

def ensure_camera_methods():
    """
    Ensure the Camera class has needed methods.
    This function patches the Camera class if methods are missing.
    """
    from core.camera import Camera
    
    # Add stop method if not present
    if not hasattr(Camera, 'stop') or not callable(getattr(Camera, 'stop', None)):
        def stop(self):
            """Stop the camera capture thread and release resources"""
            if not self.is_running:
                print("Camera is already stopped")
                return

            # Signal the thread to stop
            self.is_running = False
            
            # Wait for the thread to terminate
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)
                
            # Release OpenCV resources
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                
            print(f"Camera stopped (ID {self.camera_id})")
            
            # Clean up MediaPipe resources
            if hasattr(self, 'hands'):
                self.hands.close()
                
            # Reset frame data
            with self.lock:
                self.frame = None
                self.processed_frame = None
                self.hand_landmarks_data = None
                
        Camera.stop = stop
    
    # Add get_processed_frame method if not present
    if not hasattr(Camera, 'get_processed_frame') or not callable(getattr(Camera, 'get_processed_frame', None)):
        def get_processed_frame(self):
            """Thread-safe method to get the latest processed frame"""
            with self.lock:
                if self.processed_frame is None:
                    return None
                return self.processed_frame.copy()
        
        Camera.get_processed_frame = get_processed_frame

def main():
    # Ensure Camera class has necessary methods
    ensure_camera_methods()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GestureDrive File Navigator')
    parser.add_argument('--path', type=str, default=None, 
                        help='Initial directory path (default: current working directory)')
    parser.add_argument('--camera', type=int, default=0, 
                        help='Camera ID to use (default: 0)')
    args = parser.parse_args()
    
    # Initialize the camera with a reasonable resolution
    camera = Camera(camera_id=args.camera, width=1280, height=720, mirror=True)
    
    # Create navigator with specified or current path
    navigator = DynamicGestureNavigator(camera, args.path)
    
    try:
        # Start the camera
        camera.start()
        
        # Main application loop
        while True:
            # Get the latest frame
            frame = camera.get_processed_frame()
            if frame is None:
                time.sleep(0.01)
                continue
            
            # Update navigator state
            state = navigator.update()
            
            # Draw visualizations on the frame
            display_frame = navigator.draw_visualization(frame.copy(), state)
            
            # Show the frame
            cv2.imshow('GestureDrive File Navigator', display_frame)
            
            # Process keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('n'):
                navigator.select_next()
            elif key == ord('p'):
                navigator.select_previous()
            elif key == ord('r'):
                # Refresh directory listing
                navigator.navigator.refresh_directory()
                
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        # Clean up resources
        camera.stop()
        cv2.destroyAllWindows()
        print("Application terminated")

if __name__ == "__main__":
    main()
