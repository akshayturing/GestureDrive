# # # import cv2
# # # import threading
# # # import time
# # # import numpy as np
# # # import mediapipe as mp

# # # class Camera:
# # #     def __init__(self, camera_id=0):
# # #         self.camera_id = camera_id
# # #         self.video_capture = None
# # #         self.is_running = False
# # #         self.lock = threading.Lock()
# # #         self.frame = None
# # #         self.fps = 0
# # #         self.last_frame_time = time.time()
# # #         self.frame_count = 0
        
# # #         # MediaPipe hand detection (will be used later)
# # #         self.mp_hands = mp.solutions.hands
# # #         self.mp_drawing = mp.solutions.drawing_utils
# # #         self.hands = None
        
# # #         # Settings
# # #         self.mirror = True
# # #         self.show_landmarks = True
# # #         self.min_detection_confidence = 0.7
# # #         self.min_tracking_confidence = 0.5

# # #     def start(self):
# # #         """Initialize and start the camera capture thread"""
# # #         if self.is_running:
# # #             print("Camera is already running")
# # #             return
        
# # #         self.video_capture = cv2.VideoCapture(self.camera_id)
# # #         if not self.video_capture.isOpened():
# # #             raise ValueError(f"Unable to open camera {self.camera_id}")
            
# # #         # Set camera properties
# # #         self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# # #         self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
# # #         # Start capture thread
# # #         self.is_running = True
# # #         self.thread = threading.Thread(target=self._capture_loop)
# # #         self.thread.daemon = True
# # #         self.thread.start()
        
# # #         # Initialize MediaPipe hands
# # #         self.hands = self.mp_hands.Hands(
# # #             max_num_hands=1,
# # #             min_detection_confidence=self.min_detection_confidence,
# # #             min_tracking_confidence=self.min_tracking_confidence
# # #         )
        
# # #         print(f"Camera {self.camera_id} started")

# # #     def stop(self):
# # #         """Stop the camera capture"""
# # #         self.is_running = False
# # #         if self.thread:
# # #             self.thread.join()
# # #         if self.video_capture:
# # #             self.video_capture.release()
# # #         if self.hands:
# # #             self.hands.close()
# # #         print(f"Camera {self.camera_id} stopped")

# # #     def _capture_loop(self):
# # #         """Camera capture loop that runs in a separate thread"""
# # #         while self.is_running:
# # #             ret, frame = self.video_capture.read()
# # #             if not ret:
# # #                 print("Failed to capture frame")
# # #                 time.sleep(0.1)
# # #                 continue
                
# # #             # Calculate FPS
# # #             current_time = time.time()
# # #             self.frame_count += 1
# # #             if (current_time - self.last_frame_time) >= 1.0:
# # #                 self.fps = self.frame_count
# # #                 self.frame_count = 0
# # #                 self.last_frame_time = current_time
            
# # #             # Mirror the frame if needed
# # #             if self.mirror:
# # #                 frame = cv2.flip(frame, 1)
            
# # #             # Process the frame for hand detection (basic implementation)
# # #             self._process_frame(frame)
            
# # #             # Update the current frame (thread-safe)
# # #             with self.lock:
# # #                 self.frame = frame

# # #     def _process_frame(self, frame):
# # #         """Process the frame for hand detection and visualization"""
# # #         # Convert to RGB for MediaPipe
# # #         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
# # #         # Process with MediaPipe
# # #         if self.hands:
# # #             results = self.hands.process(rgb_frame)
            
# # #             # Draw hand landmarks if detected and enabled
# # #             if results.multi_hand_landmarks and self.show_landmarks:
# # #                 for hand_landmarks in results.multi_hand_landmarks:
# # #                     self.mp_drawing.draw_landmarks(
# # #                         frame,
# # #                         hand_landmarks,
# # #                         self.mp_hands.HAND_CONNECTIONS
# # #                     )
                    
# # #             # Add FPS counter to the frame
# # #             cv2.putText(
# # #                 frame, 
# # #                 f"FPS: {self.fps}", 
# # #                 (10, 30), 
# # #                 cv2.FONT_HERSHEY_SIMPLEX, 
# # #                 1, 
# # #                 (0, 255, 0), 
# # #                 2
# # #             )

# # #     def get_frame(self):
# # #         """Get the current frame as JPEG bytes"""
# # #         if not self.is_running:
# # #             return None
        
# # #         with self.lock:
# # #             if self.frame is None:
# # #                 return None
# # #             # Encode the frame as JPEG
# # #             ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            
# # #         return jpeg.tobytes() if ret else None

# # # # Create a camera instance for the application
# # # camera = None

# # # def init_camera(camera_id=0):
# # #     """Initialize the camera with the given ID"""
# # #     global camera
# # #     camera = Camera(camera_id)
# # #     camera.start()
# # #     return camera

# # # def get_camera():
# # #     """Get the current camera instance"""
# # #     global camera
# # #     if camera is None:
# # #         camera = init_camera()
# # #     return camera
# # import cv2
# # import threading
# # import time
# # import numpy as np
# # import mediapipe as mp
# # import os

# # class Camera:
# #     def __init__(self, camera_id=0):
# #         self.camera_id = camera_id
# #         self.video_capture = None
# #         self.is_running = False
# #         self.lock = threading.Lock()
# #         self.frame = None
# #         self.fps = 0
# #         self.last_frame_time = time.time()
# #         self.frame_count = 0
# #         self.last_error = None
# #         self.consecutive_failures = 0
        
# #         # MediaPipe hand detection
# #         self.mp_hands = mp.solutions.hands
# #         self.mp_drawing = mp.solutions.drawing_utils
# #         self.hands = None
        
# #         # Settings
# #         self.mirror = True
# #         self.show_landmarks = True
# #         self.min_detection_confidence = 0.7
# #         self.min_tracking_confidence = 0.5

# #     def start(self):
# #         """Initialize and start the camera capture thread"""
# #         if self.is_running:
# #             print("Camera is already running")
# #             return
        
# #         try:
# #             print(f"Attempting to open camera {self.camera_id}")
# #             self.video_capture = cv2.VideoCapture(self.camera_id)
            
# #             if not self.video_capture.isOpened():
# #                 self.last_error = f"Unable to open camera {self.camera_id}"
# #                 print(self.last_error)
# #                 # Try default camera as fallback
# #                 if self.camera_id != 0:
# #                     print("Trying default camera (0) as fallback")
# #                     self.camera_id = 0
# #                     self.video_capture.release()
# #                     self.video_capture = cv2.VideoCapture(0)
# #                     if not self.video_capture.isOpened():
# #                         raise ValueError(f"Unable to open default camera")
# #                 else:
# #                     raise ValueError(self.last_error)
                
# #             # Set camera properties
# #             self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# #             self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
# #             # Verify camera works by reading a test frame
# #             ret, test_frame = self.video_capture.read()
# #             if not ret or test_frame is None or test_frame.size == 0:
# #                 raise ValueError("Camera opened but unable to read frames")
                
# #             # Start capture thread
# #             self.is_running = True
# #             self.thread = threading.Thread(target=self._capture_loop)
# #             self.thread.daemon = True
# #             self.thread.start()
            
# #             # Initialize MediaPipe hands
# #             self.hands = self.mp_hands.Hands(
# #                 max_num_hands=1,
# #                 min_detection_confidence=self.min_detection_confidence,
# #                 min_tracking_confidence=self.min_tracking_confidence
# #             )
            
# #             print(f"Camera {self.camera_id} started successfully")
# #             return True
            
# #         except Exception as e:
# #             self.last_error = str(e)
# #             print(f"Camera start error: {self.last_error}")
# #             if self.video_capture:
# #                 self.video_capture.release()
# #                 self.video_capture = None
# #             return False

# #     def stop(self):
# #         """Stop the camera capture"""
# #         self.is_running = False
# #         if self.thread:
# #             self.thread.join(timeout=1.0)  # Wait up to 1 second
# #         if self.video_capture:
# #             self.video_capture.release()
# #             self.video_capture = None
# #         if self.hands:
# #             self.hands.close()
# #         print(f"Camera {self.camera_id} stopped")

# #     def _capture_loop(self):
# #         """Camera capture loop that runs in a separate thread"""
# #         print("Capture loop started")
# #         while self.is_running:
# #             if not self.video_capture or not self.video_capture.isOpened():
# #                 print("Video capture is not open in capture loop")
# #                 self.consecutive_failures += 1
# #                 time.sleep(0.1)
# #                 # Try to reopen the camera if too many failures
# #                 if self.consecutive_failures > 10:
# #                     print("Too many consecutive failures, attempting to reopen camera")
# #                     self.video_capture.release()
# #                     self.video_capture = cv2.VideoCapture(self.camera_id)
# #                     self.consecutive_failures = 0
# #                 continue
                
# #             ret, frame = self.video_capture.read()
# #             if not ret or frame is None or frame.size == 0:
# #                 print("Failed to capture frame")
# #                 self.consecutive_failures += 1
# #                 time.sleep(0.1)
# #                 continue
                
# #             self.consecutive_failures = 0  # Reset failure counter on success
            
# #             # Calculate FPS
# #             current_time = time.time()
# #             self.frame_count += 1
# #             if (current_time - self.last_frame_time) >= 1.0:
# #                 self.fps = self.frame_count
# #                 self.frame_count = 0
# #                 self.last_frame_time = current_time
# #                 print(f"FPS: {self.fps}")  # Debug output
            
# #             # Mirror the frame if needed
# #             if self.mirror:
# #                 frame = cv2.flip(frame, 1)
            
# #             # Process the frame for hand detection
# #             self._process_frame(frame)
            
# #             # Update the current frame (thread-safe)
# #             with self.lock:
# #                 self.frame = frame

# #     def _process_frame(self, frame):
# #         """Process the frame for hand detection and visualization"""
# #         if self.hands is None:
# #             return
            
# #         # Convert to RGB for MediaPipe
# #         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
# #         # Process with MediaPipe
# #         results = self.hands.process(rgb_frame)
        
# #         # Draw hand landmarks if detected and enabled
# #         if results.multi_hand_landmarks and self.show_landmarks:
# #             for hand_landmarks in results.multi_hand_landmarks:
# #                 self.mp_drawing.draw_landmarks(
# #                     frame,
# #                     hand_landmarks,
# #                     self.mp_hands.HAND_CONNECTIONS
# #                 )
                    
# #         # Add FPS counter to the frame
# #         cv2.putText(
# #             frame, 
# #             f"FPS: {self.fps}", 
# #             (10, 30), 
# #             cv2.FONT_HERSHEY_SIMPLEX, 
# #             1, 
# #             (0, 255, 0), 
# #             2
# #         )
        
# #         # Add status indicator
# #         status_text = "Running" if self.is_running else "Stopped"
# #         cv2.putText(
# #             frame, 
# #             f"Status: {status_text}", 
# #             (10, 70), 
# #             cv2.FONT_HERSHEY_SIMPLEX, 
# #             1, 
# #             (0, 255, 0), 
# #             2
# #         )

# #     def get_frame(self):
# #         """Get the current frame as JPEG bytes"""
# #         if not self.is_running:
# #             return self._get_error_frame("Camera not running")
        
# #         with self.lock:
# #             if self.frame is None:
# #                 return self._get_error_frame("No frame available")
                
# #             try:
# #                 # Encode the frame as JPEG
# #                 ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
# #                 if not ret:
# #                     return self._get_error_frame("Frame encoding failed")
# #                 return jpeg.tobytes()
# #             except Exception as e:
# #                 print(f"Error encoding frame: {str(e)}")
# #                 return self._get_error_frame(f"Encoding error: {str(e)}")
    
# #     def _get_error_frame(self, error_message):
# #         """Generate an error frame with message when regular frames aren't available"""
# #         # Create a black frame with error text
# #         frame = np.zeros((480, 640, 3), dtype=np.uint8)
# #         # Add error message
# #         cv2.putText(
# #             frame, 
# #             "Camera Error", 
# #             (150, 200), 
# #             cv2.FONT_HERSHEY_SIMPLEX, 
# #             1, 
# #             (0, 0, 255), 
# #             2
# #         )
# #         cv2.putText(
# #             frame, 
# #             error_message, 
# #             (50, 250), 
# #             cv2.FONT_HERSHEY_SIMPLEX, 
# #             0.8, 
# #             (255, 255, 255), 
# #             1
# #         )
        
# #         # Encode the error frame
# #         ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
# #         return jpeg.tobytes() if ret else None
    
# #     def get_status(self):
# #         """Get current camera status"""
# #         return {
# #             "running": self.is_running,
# #             "fps": self.fps,
# #             "error": self.last_error,
# #             "camera_id": self.camera_id
# #         }

# # # Camera instance
# # camera = None

# # def init_camera(camera_id=0):
# #     """Initialize the camera with the given ID"""
# #     global camera
# #     if camera is not None:
# #         camera.stop()  # Stop any existing camera
    
# #     camera = Camera(camera_id)
# #     success = camera.start()
# #     if not success:
# #         print(f"Failed to start camera {camera_id}: {camera.last_error}")
# #     return camera

# # def get_camera():
# #     """Get the current camera instance"""
# #     global camera
# #     if camera is None:
# #         camera = init_camera()
# #     return camera
# import cv2
# import threading
# import time
# import numpy as np
# import mediapipe as mp
# import os
# import atexit
# import signal
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO, 
#                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger('camera')

# class Camera:
#     def __init__(self, camera_id=0):
#         self.camera_id = camera_id
#         self.video_capture = None
#         self.is_running = False
#         self.lock = threading.Lock()
#         self.frame = None
#         self.fps = 0
#         self.last_frame_time = time.time()
#         self.frame_count = 0
#         self.last_error = None
#         self.consecutive_failures = 0
#         self.thread = None
        
#         # MediaPipe hand detection
#         self.mp_hands = mp.solutions.hands
#         self.mp_drawing = mp.solutions.drawing_utils
#         self.hands = None
        
#         # Settings
#         self.mirror = True
#         self.show_landmarks = True
#         self.min_detection_confidence = 0.7
#         self.min_tracking_confidence = 0.5
        
#         logger.info(f"Camera instance created with ID: {camera_id}")
        
#         # Register this instance for cleanup
#         _register_camera_instance(self)

#     def __del__(self):
#         """Destructor to ensure resources are released"""
#         self.cleanup()
#         logger.info("Camera instance destroyed")

#     def start(self):
#         """Initialize and start the camera capture thread"""
#         if self.is_running:
#             logger.info("Camera is already running")
#             return True
        
#         try:
#             logger.info(f"Attempting to open camera {self.camera_id}")
#             self.video_capture = cv2.VideoCapture(self.camera_id)
            
#             if not self.video_capture.isOpened():
#                 self.last_error = f"Unable to open camera {self.camera_id}"
#                 logger.error(self.last_error)
#                 # Try default camera as fallback
#                 if self.camera_id != 0:
#                     logger.info("Trying default camera (0) as fallback")
#                     self.camera_id = 0
#                     self.video_capture.release()
#                     self.video_capture = cv2.VideoCapture(0)
#                     if not self.video_capture.isOpened():
#                         raise ValueError(f"Unable to open default camera")
#                 else:
#                     raise ValueError(self.last_error)
                
#             # Set camera properties
#             self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#             self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
#             # Verify camera works by reading a test frame
#             ret, test_frame = self.video_capture.read()
#             if not ret or test_frame is None or test_frame.size == 0:
#                 raise ValueError("Camera opened but unable to read frames")
                
#             # Start capture thread
#             self.is_running = True
#             self.thread = threading.Thread(target=self._capture_loop)
#             self.thread.daemon = True
#             self.thread.start()
            
#             # Initialize MediaPipe hands
#             self.hands = self.mp_hands.Hands(
#                 max_num_hands=1,
#                 min_detection_confidence=self.min_detection_confidence,
#                 min_tracking_confidence=self.min_tracking_confidence
#             )
            
#             logger.info(f"Camera {self.camera_id} started successfully")
#             return True
            
#         except Exception as e:
#             self.last_error = str(e)
#             logger.error(f"Camera start error: {self.last_error}")
#             self.cleanup()
#             return False

#     def stop(self):
#         """Stop the camera capture"""
#         logger.info(f"Stopping camera {self.camera_id}")
#         self.is_running = False
#         self.cleanup()

#     def cleanup(self):
#         """Release all resources associated with the camera"""
#         logger.info(f"Cleaning up camera resources for camera {self.camera_id}")
        
#         # Stop the thread first
#         if hasattr(self, 'thread') and self.thread and self.thread.is_alive():
#             logger.info("Waiting for capture thread to terminate...")
#             self.is_running = False
#             self.thread.join(timeout=2.0)  # Wait up to 2 seconds
#             if self.thread.is_alive():
#                 logger.warning("Capture thread did not terminate in time")
        
#         # Release camera resources
#         if hasattr(self, 'video_capture') and self.video_capture:
#             logger.info("Releasing video capture resource")
#             try:
#                 self.video_capture.release()
#             except Exception as e:
#                 logger.error(f"Error releasing video capture: {e}")
#             finally:
#                 self.video_capture = None
                
#         # Close MediaPipe resources
#         if hasattr(self, 'hands') and self.hands:
#             logger.info("Closing MediaPipe hands resource")
#             try:
#                 self.hands.close()
#             except Exception as e:
#                 logger.error(f"Error closing MediaPipe hands: {e}")
#             finally:
#                 self.hands = None
                
#         # Close any OpenCV windows that might be open
#         try:
#             cv2.destroyAllWindows()
#             # Some systems need this to fully close windows
#             for i in range(5):
#                 cv2.waitKey(1)
#         except Exception as e:
#             logger.error(f"Error closing OpenCV windows: {e}")
            
#         # Reset state variables
#         self.is_running = False
#         self.frame = None
#         self.fps = 0
        
#         logger.info("Camera cleanup completed")

#     def _capture_loop(self):
#         """Camera capture loop that runs in a separate thread"""
#         logger.info("Capture loop started")
#         while self.is_running:
#             if not self.video_capture or not self.video_capture.isOpened():
#                 logger.warning("Video capture is not open in capture loop")
#                 self.consecutive_failures += 1
#                 time.sleep(0.1)
#                 # Try to reopen the camera if too many failures
#                 if self.consecutive_failures > 10:
#                     logger.info("Too many consecutive failures, attempting to reopen camera")
#                     if self.video_capture:
#                         self.video_capture.release()
#                     self.video_capture = cv2.VideoCapture(self.camera_id)
#                     self.consecutive_failures = 0
#                 continue
                
#             ret, frame = self.video_capture.read()
#             if not ret or frame is None or frame.size == 0:
#                 logger.warning("Failed to capture frame")
#                 self.consecutive_failures += 1
#                 time.sleep(0.1)
#                 continue
                
#             self.consecutive_failures = 0  # Reset failure counter on success
            
#             # Calculate FPS
#             current_time = time.time()
#             self.frame_count += 1
#             if (current_time - self.last_frame_time) >= 1.0:
#                 self.fps = self.frame_count
#                 self.frame_count = 0
#                 self.last_frame_time = current_time
#                 logger.debug(f"FPS: {self.fps}")
            
#             # Mirror the frame if needed
#             if self.mirror:
#                 frame = cv2.flip(frame, 1)
            
#             # Process the frame for hand detection
#             self._process_frame(frame)
            
#             # Update the current frame (thread-safe)
#             with self.lock:
#                 self.frame = frame

#         logger.info("Capture loop ended")

#     def _process_frame(self, frame):
#         """Process the frame for hand detection and visualization"""
#         if self.hands is None:
#             return
            
#         # Convert to RGB for MediaPipe
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#         # Process with MediaPipe
#         results = self.hands.process(rgb_frame)
        
#         # Draw hand landmarks if detected and enabled
#         if results.multi_hand_landmarks and self.show_landmarks:
#             for hand_landmarks in results.multi_hand_landmarks:
#                 self.mp_drawing.draw_landmarks(
#                     frame,
#                     hand_landmarks,
#                     self.mp_hands.HAND_CONNECTIONS
#                 )
                    
#         # Add FPS counter to the frame
#         cv2.putText(
#             frame, 
#             f"FPS: {self.fps}", 
#             (10, 30), 
#             cv2.FONT_HERSHEY_SIMPLEX, 
#             1, 
#             (0, 255, 0), 
#             2
#         )
        
#         # Add status indicator
#         status_text = "Running" if self.is_running else "Stopped"
#         cv2.putText(
#             frame, 
#             f"Status: {status_text}", 
#             (10, 70), 
#             cv2.FONT_HERSHEY_SIMPLEX, 
#             1, 
#             (0, 255, 0), 
#             2
#         )

#     def get_frame(self):
#         """Get the current frame as JPEG bytes"""
#         if not self.is_running:
#             return self._get_error_frame("Camera not running")
        
#         with self.lock:
#             if self.frame is None:
#                 return self._get_error_frame("No frame available")
                
#             try:
#                 # Encode the frame as JPEG
#                 ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
#                 if not ret:
#                     return self._get_error_frame("Frame encoding failed")
#                 return jpeg.tobytes()
#             except Exception as e:
#                 logger.error(f"Error encoding frame: {str(e)}")
#                 return self._get_error_frame(f"Encoding error: {str(e)}")
    
#     def _get_error_frame(self, error_message):
#         """Generate an error frame with message when regular frames aren't available"""
#         # Create a black frame with error text
#         frame = np.zeros((480, 640, 3), dtype=np.uint8)
#         # Add error message
#         cv2.putText(
#             frame, 
#             "Camera Error", 
#             (150, 200), 
#             cv2.FONT_HERSHEY_SIMPLEX, 
#             1, 
#             (0, 0, 255), 
#             2
#         )
#         cv2.putText(
#             frame, 
#             error_message, 
#             (50, 250), 
#             cv2.FONT_HERSHEY_SIMPLEX, 
#             0.8, 
#             (255, 255, 255), 
#             1
#         )
        
#         # Encode the error frame
#         ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
#         return jpeg.tobytes() if ret else None
    
#     def get_status(self):
#         """Get current camera status"""
#         return {
#             "running": self.is_running,
#             "fps": self.fps,
#             "error": self.last_error,
#             "camera_id": self.camera_id
#         }

# # Global registry of active camera instances
# _active_cameras = []

# def _register_camera_instance(camera):
#     """Register a camera instance for global cleanup"""
#     global _active_cameras
#     _active_cameras.append(camera)
#     logger.info(f"Registered camera instance. Active cameras: {len(_active_cameras)}")

# def _cleanup_all_cameras():
#     """Clean up all registered camera instances"""
#     global _active_cameras
#     logger.info(f"Cleaning up all cameras ({len(_active_cameras)} active)")
#     for cam in _active_cameras:
#         try:
#             cam.cleanup()
#         except Exception as e:
#             logger.error(f"Error during camera cleanup: {e}")
#     _active_cameras.clear()
#     logger.info("All cameras cleaned up")

# # Register cleanup handlers for unexpected termination
# atexit.register(_cleanup_all_cameras)

# # Register signal handlers for graceful shutdown
# for sig in [signal.SIGINT, signal.SIGTERM]:
#     signal.signal(sig, lambda s, f: (_cleanup_all_cameras(), signal.default_int_handler(s, f)))

# # Camera instance
# camera = None

# def init_camera(camera_id=0):
#     """Initialize the camera with the given ID"""
#     global camera
#     if camera is not None:
#         camera.stop()  # Stop any existing camera
    
#     camera = Camera(camera_id)
#     success = camera.start()
#     if not success:
#         logger.error(f"Failed to start camera {camera_id}: {camera.last_error}")
#     return camera

# def get_camera():
#     """Get the current camera instance"""
#     global camera
#     if camera is None:
#         camera = init_camera()
#     return camera

# def cleanup_camera():
#     """Clean up the global camera instance"""
#     global camera
#     if camera:
#         logger.info("Cleaning up global camera instance")
#         camera.cleanup()
#         camera = None
import cv2
import mediapipe as mp
import numpy as np
import time
import threading

class Camera:
    def __init__(self, camera_id=0, width=640, height=480, mirror=True, min_detection_confidence=0.7):
        # Camera parameters
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.mirror = mirror
        
        # MediaPipe initialization
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence
        )
        
        # Frame handling
        self.frame = None
        self.processed_frame = None
        self.lock = threading.Lock()
        
        # Configuration flags
        self.show_landmarks = True
        self.hand_landmarks_data = None
        
        # FPS calculation
        self.fps = 0
        self.prev_frame_time = 0
        self.new_frame_time = 0
        
        # Thread management
        self.is_running = False
        self.thread = None
    
    def start(self):
        """Start the camera capture thread"""
        if self.is_running:
            print("Camera is already running")
            return
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(self.camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera with ID {self.camera_id}")
        
        # Start the capture thread
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()
        print(f"Camera started with ID {self.camera_id}")
        
    def _capture_loop(self):
        """Main capture loop that runs in a separate thread"""
        while self.is_running:
            # Read a new frame from the video stream
            ret, frame = self.cap.read()
            
            if not ret:
                print("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Mirror the frame if enabled
            if self.mirror:
                frame = cv2.flip(frame, 1)
            
            # Calculate FPS
            self.new_frame_time = time.time()
            self.fps = 1 / (self.new_frame_time - self.prev_frame_time) if self.prev_frame_time > 0 else 0
            self.prev_frame_time = self.new_frame_time
            
            # Process the frame with MediaPipe
            processed = self._process_frame(frame.copy())
            
            # Thread-safe update of the current frame
            with self.lock:
                self.frame = frame.copy()
                self.processed_frame = processed
            
            # Slight sleep to reduce CPU usage
            time.sleep(0.01)
    
    def _process_frame(self, frame):
        """Process frame to detect hands and draw landmarks"""
        # Convert BGR to RGB for MediaPipe (MediaPipe requires RGB input)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the RGB frame with MediaPipe
        results = self.hands.process(rgb_frame)
        
        # Store the hand landmarks data for external use
        self.hand_landmarks_data = results.multi_hand_landmarks
        
        # Create a copy of the frame to draw on
        annotated_frame = frame.copy()
        
        # Draw FPS information
        cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Draw hand landmarks if enabled
        if self.show_landmarks and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw the hand landmarks
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
        
        # Return the processed frame with annotations
        return annotated_frame
    
    def get_frame(self, processed=True):
        """Return the current frame (processed or raw)"""
        with self.lock:
            if processed and self.processed_frame is not None:
                return self.processed_frame.copy()
            elif self.frame is not None:
                return self.frame.copy()
            return None
    
    def get_jpeg_frame(self, processed=True):
        """Return JPEG encoded frame for web streaming"""
        frame = self.get_frame(processed)
        if frame is None:
            # Return a blank frame if no frame is available
            blank = np.zeros((self.height, self.width, 3), np.uint8)
            _, jpeg = cv2.imencode('.jpg', blank)
            return jpeg.tobytes()
        
        _, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
    
    def get_hand_landmarks(self):
        """Return the current hand landmarks data"""
        return self.hand_landmarks_data
    
    def stop(self):
        """Stop the camera and release resources"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
