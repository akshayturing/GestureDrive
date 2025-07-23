# persistent_gesture_explorer.py

import cv2
import time
import os
import argparse
import threading
from pathlib import Path

from camera import Camera
from persistent_gesture_navigator import PersistentGestureNavigator

def ensure_camera_methods():
    """Add required methods to the Camera class if they don't exist."""
    from camera import Camera
    
    # Add stop method if needed
    if not hasattr(Camera, 'stop') or not callable(getattr(Camera, 'stop', None)):
        def stop(self):
            """Stop the camera capture and release resources."""
            if not self.is_running:
                return
                
            self.is_running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)
                
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                
            # Clean up MediaPipe resources
            if hasattr(self, 'hands'):
                self.hands.close()
        
        Camera.stop = stop
    
    # Add get_processed_frame method if needed
    if not hasattr(Camera, 'get_processed_frame') or not callable(getattr(Camera, 'get_processed_frame', None)):
        def get_processed_frame(self):
            """Get the latest processed frame safely."""
            with self.lock:
                if self.processed_frame is None:
                    return None
                return self.processed_frame.copy()
        
        Camera.get_processed_frame = get_processed_frame

def main():
    # Ensure Camera class has required methods
    ensure_camera_methods()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Persistent Gesture File Explorer')
    parser.add_argument('--path', type=str, default=None, 
                        help='Initial directory path')
    parser.add_argument('--camera', type=int, default=0, 
                        help='Camera ID to use')
    args = parser.parse_args()
    
    # Initialize camera
    camera = Camera(camera_id=args.camera, width=1280, height=720, mirror=True)
    
    # Initialize persistent navigator
    navigator = PersistentGestureNavigator(camera, args.path)
    
    try:
        # Start camera
        camera.start()
        
        # Main application loop
        while True:
            # Get the latest processed frame
            frame = camera.get_processed_frame()
            if frame is None:
                time.sleep(0.01)
                continue
                
            # Update navigator state
            state = navigator.update()
            
            # Draw UI on frame
            display_frame = navigator.draw_ui(frame.copy())
            
            # Show the frame
            cv2.imshow('Persistent Gesture File Explorer', display_frame)
            
            # Process keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('n'):
                navigator.select_next()
            elif key == ord('p'):
                navigator.select_previous()
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        navigator.shutdown()
        camera.stop()
        cv2.destroyAllWindows()
        print("Application terminated cleanly")

if __name__ == "__main__":
    main()