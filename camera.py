# # # # import cv2
# # # # import threading
# # # # import time
# # # # import numpy as np
# # # # import mediapipe as mp

# # # # class Camera:
# # # #     def __init__(self, camera_id=0):
# # # #         self.camera_id = camera_id
# # # #         self.video_capture = None
# # # #         self.is_running = False
# # # #         self.lock = threading.Lock()
# # # #         self.frame = None
# # # #         self.fps = 0
# # # #         self.last_frame_time = time.time()
# # # #         self.frame_count = 0
        
# # # #         # MediaPipe hand detection (will be used later)
# # # #         self.mp_hands = mp.solutions.hands
# # # #         self.mp_drawing = mp.solutions.drawing_utils
# # # #         self.hands = None
        
# # # #         # Settings
# # # #         self.mirror = True
# # # #         self.show_landmarks = True
# # # #         self.min_detection_confidence = 0.7
# # # #         self.min_tracking_confidence = 0.5

# # # #     def start(self):
# # # #         """Initialize and start the camera capture thread"""
# # # #         if self.is_running:
# # # #             print("Camera is already running")
# # # #             return
        
# # # #         self.video_capture = cv2.VideoCapture(self.camera_id)
# # # #         if not self.video_capture.isOpened():
# # # #             raise ValueError(f"Unable to open camera {self.camera_id}")
            
# # # #         # Set camera properties
# # # #         self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# # # #         self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
# # # #         # Start capture thread
# # # #         self.is_running = True
# # # #         self.thread = threading.Thread(target=self._capture_loop)
# # # #         self.thread.daemon = True
# # # #         self.thread.start()
        
# # # #         # Initialize MediaPipe hands
# # # #         self.hands = self.mp_hands.Hands(
# # # #             max_num_hands=1,
# # # #             min_detection_confidence=self.min_detection_confidence,
# # # #             min_tracking_confidence=self.min_tracking_confidence
# # # #         )
        
# # # #         print(f"Camera {self.camera_id} started")

# # # #     def stop(self):
# # # #         """Stop the camera capture"""
# # # #         self.is_running = False
# # # #         if self.thread:
# # # #             self.thread.join()
# # # #         if self.video_capture:
# # # #             self.video_capture.release()
# # # #         if self.hands:
# # # #             self.hands.close()
# # # #         print(f"Camera {self.camera_id} stopped")

# # # #     def _capture_loop(self):
# # # #         """Camera capture loop that runs in a separate thread"""
# # # #         while self.is_running:
# # # #             ret, frame = self.video_capture.read()
# # # #             if not ret:
# # # #                 print("Failed to capture frame")
# # # #                 time.sleep(0.1)
# # # #                 continue
                
# # # #             # Calculate FPS
# # # #             current_time = time.time()
# # # #             self.frame_count += 1
# # # #             if (current_time - self.last_frame_time) >= 1.0:
# # # #                 self.fps = self.frame_count
# # # #                 self.frame_count = 0
# # # #                 self.last_frame_time = current_time
            
# # # #             # Mirror the frame if needed
# # # #             if self.mirror:
# # # #                 frame = cv2.flip(frame, 1)
            
# # # #             # Process the frame for hand detection (basic implementation)
# # # #             self._process_frame(frame)
            
# # # #             # Update the current frame (thread-safe)
# # # #             with self.lock:
# # # #                 self.frame = frame

# # # #     def _process_frame(self, frame):
# # # #         """Process the frame for hand detection and visualization"""
# # # #         # Convert to RGB for MediaPipe
# # # #         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
# # # #         # Process with MediaPipe
# # # #         if self.hands:
# # # #             results = self.hands.process(rgb_frame)
            
# # # #             # Draw hand landmarks if detected and enabled
# # # #             if results.multi_hand_landmarks and self.show_landmarks:
# # # #                 for hand_landmarks in results.multi_hand_landmarks:
# # # #                     self.mp_drawing.draw_landmarks(
# # # #                         frame,
# # # #                         hand_landmarks,
# # # #                         self.mp_hands.HAND_CONNECTIONS
# # # #                     )
                    
# # # #             # Add FPS counter to the frame
# # # #             cv2.putText(
# # # #                 frame, 
# # # #                 f"FPS: {self.fps}", 
# # # #                 (10, 30), 
# # # #                 cv2.FONT_HERSHEY_SIMPLEX, 
# # # #                 1, 
# # # #                 (0, 255, 0), 
# # # #                 2
# # # #             )

# # # #     def get_frame(self):
# # # #         """Get the current frame as JPEG bytes"""
# # # #         if not self.is_running:
# # # #             return None
        
# # # #         with self.lock:
# # # #             if self.frame is None:
# # # #                 return None
# # # #             # Encode the frame as JPEG
# # # #             ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            
# # # #         return jpeg.tobytes() if ret else None

# # # # # Create a camera instance for the application
# # # # camera = None

# # # # def init_camera(camera_id=0):
# # # #     """Initialize the camera with the given ID"""
# # # #     global camera
# # # #     camera = Camera(camera_id)
# # # #     camera.start()
# # # #     return camera

# # # # def get_camera():
# # # #     """Get the current camera instance"""
# # # #     global camera
# # # #     if camera is None:
# # # #         camera = init_camera()
# # # #     return camera
# # # import cv2
# # # import threading
# # # import time
# # # import numpy as np
# # # import mediapipe as mp
# # # import os

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
# # #         self.last_error = None
# # #         self.consecutive_failures = 0
        
# # #         # MediaPipe hand detection
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
        
# # #         try:
# # #             print(f"Attempting to open camera {self.camera_id}")
# # #             self.video_capture = cv2.VideoCapture(self.camera_id)
            
# # #             if not self.video_capture.isOpened():
# # #                 self.last_error = f"Unable to open camera {self.camera_id}"
# # #                 print(self.last_error)
# # #                 # Try default camera as fallback
# # #                 if self.camera_id != 0:
# # #                     print("Trying default camera (0) as fallback")
# # #                     self.camera_id = 0
# # #                     self.video_capture.release()
# # #                     self.video_capture = cv2.VideoCapture(0)
# # #                     if not self.video_capture.isOpened():
# # #                         raise ValueError(f"Unable to open default camera")
# # #                 else:
# # #                     raise ValueError(self.last_error)
                
# # #             # Set camera properties
# # #             self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# # #             self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
# # #             # Verify camera works by reading a test frame
# # #             ret, test_frame = self.video_capture.read()
# # #             if not ret or test_frame is None or test_frame.size == 0:
# # #                 raise ValueError("Camera opened but unable to read frames")
                
# # #             # Start capture thread
# # #             self.is_running = True
# # #             self.thread = threading.Thread(target=self._capture_loop)
# # #             self.thread.daemon = True
# # #             self.thread.start()
            
# # #             # Initialize MediaPipe hands
# # #             self.hands = self.mp_hands.Hands(
# # #                 max_num_hands=1,
# # #                 min_detection_confidence=self.min_detection_confidence,
# # #                 min_tracking_confidence=self.min_tracking_confidence
# # #             )
            
# # #             print(f"Camera {self.camera_id} started successfully")
# # #             return True
            
# # #         except Exception as e:
# # #             self.last_error = str(e)
# # #             print(f"Camera start error: {self.last_error}")
# # #             if self.video_capture:
# # #                 self.video_capture.release()
# # #                 self.video_capture = None
# # #             return False

# # #     def stop(self):
# # #         """Stop the camera capture"""
# # #         self.is_running = False
# # #         if self.thread:
# # #             self.thread.join(timeout=1.0)  # Wait up to 1 second
# # #         if self.video_capture:
# # #             self.video_capture.release()
# # #             self.video_capture = None
# # #         if self.hands:
# # #             self.hands.close()
# # #         print(f"Camera {self.camera_id} stopped")

# # #     def _capture_loop(self):
# # #         """Camera capture loop that runs in a separate thread"""
# # #         print("Capture loop started")
# # #         while self.is_running:
# # #             if not self.video_capture or not self.video_capture.isOpened():
# # #                 print("Video capture is not open in capture loop")
# # #                 self.consecutive_failures += 1
# # #                 time.sleep(0.1)
# # #                 # Try to reopen the camera if too many failures
# # #                 if self.consecutive_failures > 10:
# # #                     print("Too many consecutive failures, attempting to reopen camera")
# # #                     self.video_capture.release()
# # #                     self.video_capture = cv2.VideoCapture(self.camera_id)
# # #                     self.consecutive_failures = 0
# # #                 continue
                
# # #             ret, frame = self.video_capture.read()
# # #             if not ret or frame is None or frame.size == 0:
# # #                 print("Failed to capture frame")
# # #                 self.consecutive_failures += 1
# # #                 time.sleep(0.1)
# # #                 continue
                
# # #             self.consecutive_failures = 0  # Reset failure counter on success
            
# # #             # Calculate FPS
# # #             current_time = time.time()
# # #             self.frame_count += 1
# # #             if (current_time - self.last_frame_time) >= 1.0:
# # #                 self.fps = self.frame_count
# # #                 self.frame_count = 0
# # #                 self.last_frame_time = current_time
# # #                 print(f"FPS: {self.fps}")  # Debug output
            
# # #             # Mirror the frame if needed
# # #             if self.mirror:
# # #                 frame = cv2.flip(frame, 1)
            
# # #             # Process the frame for hand detection
# # #             self._process_frame(frame)
            
# # #             # Update the current frame (thread-safe)
# # #             with self.lock:
# # #                 self.frame = frame

# # #     def _process_frame(self, frame):
# # #         """Process the frame for hand detection and visualization"""
# # #         if self.hands is None:
# # #             return
            
# # #         # Convert to RGB for MediaPipe
# # #         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
# # #         # Process with MediaPipe
# # #         results = self.hands.process(rgb_frame)
        
# # #         # Draw hand landmarks if detected and enabled
# # #         if results.multi_hand_landmarks and self.show_landmarks:
# # #             for hand_landmarks in results.multi_hand_landmarks:
# # #                 self.mp_drawing.draw_landmarks(
# # #                     frame,
# # #                     hand_landmarks,
# # #                     self.mp_hands.HAND_CONNECTIONS
# # #                 )
                    
# # #         # Add FPS counter to the frame
# # #         cv2.putText(
# # #             frame, 
# # #             f"FPS: {self.fps}", 
# # #             (10, 30), 
# # #             cv2.FONT_HERSHEY_SIMPLEX, 
# # #             1, 
# # #             (0, 255, 0), 
# # #             2
# # #         )
        
# # #         # Add status indicator
# # #         status_text = "Running" if self.is_running else "Stopped"
# # #         cv2.putText(
# # #             frame, 
# # #             f"Status: {status_text}", 
# # #             (10, 70), 
# # #             cv2.FONT_HERSHEY_SIMPLEX, 
# # #             1, 
# # #             (0, 255, 0), 
# # #             2
# # #         )

# # #     def get_frame(self):
# # #         """Get the current frame as JPEG bytes"""
# # #         if not self.is_running:
# # #             return self._get_error_frame("Camera not running")
        
# # #         with self.lock:
# # #             if self.frame is None:
# # #                 return self._get_error_frame("No frame available")
                
# # #             try:
# # #                 # Encode the frame as JPEG
# # #                 ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
# # #                 if not ret:
# # #                     return self._get_error_frame("Frame encoding failed")
# # #                 return jpeg.tobytes()
# # #             except Exception as e:
# # #                 print(f"Error encoding frame: {str(e)}")
# # #                 return self._get_error_frame(f"Encoding error: {str(e)}")
    
# # #     def _get_error_frame(self, error_message):
# # #         """Generate an error frame with message when regular frames aren't available"""
# # #         # Create a black frame with error text
# # #         frame = np.zeros((480, 640, 3), dtype=np.uint8)
# # #         # Add error message
# # #         cv2.putText(
# # #             frame, 
# # #             "Camera Error", 
# # #             (150, 200), 
# # #             cv2.FONT_HERSHEY_SIMPLEX, 
# # #             1, 
# # #             (0, 0, 255), 
# # #             2
# # #         )
# # #         cv2.putText(
# # #             frame, 
# # #             error_message, 
# # #             (50, 250), 
# # #             cv2.FONT_HERSHEY_SIMPLEX, 
# # #             0.8, 
# # #             (255, 255, 255), 
# # #             1
# # #         )
        
# # #         # Encode the error frame
# # #         ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
# # #         return jpeg.tobytes() if ret else None
    
# # #     def get_status(self):
# # #         """Get current camera status"""
# # #         return {
# # #             "running": self.is_running,
# # #             "fps": self.fps,
# # #             "error": self.last_error,
# # #             "camera_id": self.camera_id
# # #         }

# # # # Camera instance
# # # camera = None

# # # def init_camera(camera_id=0):
# # #     """Initialize the camera with the given ID"""
# # #     global camera
# # #     if camera is not None:
# # #         camera.stop()  # Stop any existing camera
    
# # #     camera = Camera(camera_id)
# # #     success = camera.start()
# # #     if not success:
# # #         print(f"Failed to start camera {camera_id}: {camera.last_error}")
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
# # import atexit
# # import signal
# # import logging

# # # Configure logging
# # logging.basicConfig(level=logging.INFO, 
# #                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# # logger = logging.getLogger('camera')

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
# #         self.thread = None
        
# #         # MediaPipe hand detection
# #         self.mp_hands = mp.solutions.hands
# #         self.mp_drawing = mp.solutions.drawing_utils
# #         self.hands = None
        
# #         # Settings
# #         self.mirror = True
# #         self.show_landmarks = True
# #         self.min_detection_confidence = 0.7
# #         self.min_tracking_confidence = 0.5
        
# #         logger.info(f"Camera instance created with ID: {camera_id}")
        
# #         # Register this instance for cleanup
# #         _register_camera_instance(self)

# #     def __del__(self):
# #         """Destructor to ensure resources are released"""
# #         self.cleanup()
# #         logger.info("Camera instance destroyed")

# #     def start(self):
# #         """Initialize and start the camera capture thread"""
# #         if self.is_running:
# #             logger.info("Camera is already running")
# #             return True
        
# #         try:
# #             logger.info(f"Attempting to open camera {self.camera_id}")
# #             self.video_capture = cv2.VideoCapture(self.camera_id)
            
# #             if not self.video_capture.isOpened():
# #                 self.last_error = f"Unable to open camera {self.camera_id}"
# #                 logger.error(self.last_error)
# #                 # Try default camera as fallback
# #                 if self.camera_id != 0:
# #                     logger.info("Trying default camera (0) as fallback")
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
            
# #             logger.info(f"Camera {self.camera_id} started successfully")
# #             return True
            
# #         except Exception as e:
# #             self.last_error = str(e)
# #             logger.error(f"Camera start error: {self.last_error}")
# #             self.cleanup()
# #             return False

# #     def stop(self):
# #         """Stop the camera capture"""
# #         logger.info(f"Stopping camera {self.camera_id}")
# #         self.is_running = False
# #         self.cleanup()

# #     def cleanup(self):
# #         """Release all resources associated with the camera"""
# #         logger.info(f"Cleaning up camera resources for camera {self.camera_id}")
        
# #         # Stop the thread first
# #         if hasattr(self, 'thread') and self.thread and self.thread.is_alive():
# #             logger.info("Waiting for capture thread to terminate...")
# #             self.is_running = False
# #             self.thread.join(timeout=2.0)  # Wait up to 2 seconds
# #             if self.thread.is_alive():
# #                 logger.warning("Capture thread did not terminate in time")
        
# #         # Release camera resources
# #         if hasattr(self, 'video_capture') and self.video_capture:
# #             logger.info("Releasing video capture resource")
# #             try:
# #                 self.video_capture.release()
# #             except Exception as e:
# #                 logger.error(f"Error releasing video capture: {e}")
# #             finally:
# #                 self.video_capture = None
                
# #         # Close MediaPipe resources
# #         if hasattr(self, 'hands') and self.hands:
# #             logger.info("Closing MediaPipe hands resource")
# #             try:
# #                 self.hands.close()
# #             except Exception as e:
# #                 logger.error(f"Error closing MediaPipe hands: {e}")
# #             finally:
# #                 self.hands = None
                
# #         # Close any OpenCV windows that might be open
# #         try:
# #             cv2.destroyAllWindows()
# #             # Some systems need this to fully close windows
# #             for i in range(5):
# #                 cv2.waitKey(1)
# #         except Exception as e:
# #             logger.error(f"Error closing OpenCV windows: {e}")
            
# #         # Reset state variables
# #         self.is_running = False
# #         self.frame = None
# #         self.fps = 0
        
# #         logger.info("Camera cleanup completed")

# #     def _capture_loop(self):
# #         """Camera capture loop that runs in a separate thread"""
# #         logger.info("Capture loop started")
# #         while self.is_running:
# #             if not self.video_capture or not self.video_capture.isOpened():
# #                 logger.warning("Video capture is not open in capture loop")
# #                 self.consecutive_failures += 1
# #                 time.sleep(0.1)
# #                 # Try to reopen the camera if too many failures
# #                 if self.consecutive_failures > 10:
# #                     logger.info("Too many consecutive failures, attempting to reopen camera")
# #                     if self.video_capture:
# #                         self.video_capture.release()
# #                     self.video_capture = cv2.VideoCapture(self.camera_id)
# #                     self.consecutive_failures = 0
# #                 continue
                
# #             ret, frame = self.video_capture.read()
# #             if not ret or frame is None or frame.size == 0:
# #                 logger.warning("Failed to capture frame")
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
# #                 logger.debug(f"FPS: {self.fps}")
            
# #             # Mirror the frame if needed
# #             if self.mirror:
# #                 frame = cv2.flip(frame, 1)
            
# #             # Process the frame for hand detection
# #             self._process_frame(frame)
            
# #             # Update the current frame (thread-safe)
# #             with self.lock:
# #                 self.frame = frame

# #         logger.info("Capture loop ended")

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
# #                 logger.error(f"Error encoding frame: {str(e)}")
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

# # # Global registry of active camera instances
# # _active_cameras = []

# # def _register_camera_instance(camera):
# #     """Register a camera instance for global cleanup"""
# #     global _active_cameras
# #     _active_cameras.append(camera)
# #     logger.info(f"Registered camera instance. Active cameras: {len(_active_cameras)}")

# # def _cleanup_all_cameras():
# #     """Clean up all registered camera instances"""
# #     global _active_cameras
# #     logger.info(f"Cleaning up all cameras ({len(_active_cameras)} active)")
# #     for cam in _active_cameras:
# #         try:
# #             cam.cleanup()
# #         except Exception as e:
# #             logger.error(f"Error during camera cleanup: {e}")
# #     _active_cameras.clear()
# #     logger.info("All cameras cleaned up")

# # # Register cleanup handlers for unexpected termination
# # atexit.register(_cleanup_all_cameras)

# # # Register signal handlers for graceful shutdown
# # for sig in [signal.SIGINT, signal.SIGTERM]:
# #     signal.signal(sig, lambda s, f: (_cleanup_all_cameras(), signal.default_int_handler(s, f)))

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
# #         logger.error(f"Failed to start camera {camera_id}: {camera.last_error}")
# #     return camera

# # def get_camera():
# #     """Get the current camera instance"""
# #     global camera
# #     if camera is None:
# #         camera = init_camera()
# #     return camera

# # def cleanup_camera():
# #     """Clean up the global camera instance"""
# #     global camera
# #     if camera:
# #         logger.info("Cleaning up global camera instance")
# #         camera.cleanup()
# #         camera = None
# import cv2
# import mediapipe as mp
# import numpy as np
# import time
# import threading

# class Camera:
#     def __init__(self, camera_id=0, width=640, height=480, mirror=True, min_detection_confidence=0.7):
#         # Camera parameters
#         self.camera_id = camera_id
#         self.width = width
#         self.height = height
#         self.mirror = mirror
        
#         # MediaPipe initialization
#         self.mp_hands = mp.solutions.hands
#         self.mp_drawing = mp.solutions.drawing_utils
#         self.mp_drawing_styles = mp.solutions.drawing_styles
#         self.hands = self.mp_hands.Hands(
#             static_image_mode=False,
#             max_num_hands=2,
#             min_detection_confidence=min_detection_confidence
#         )
        
#         # Frame handling
#         self.frame = None
#         self.processed_frame = None
#         self.lock = threading.Lock()
        
#         # Configuration flags
#         self.show_landmarks = True
#         self.hand_landmarks_data = None
        
#         # FPS calculation
#         self.fps = 0
#         self.prev_frame_time = 0
#         self.new_frame_time = 0
        
#         # Thread management
#         self.is_running = False
#         self.thread = None
    
#         # Add tracking stability parameters
#         self.landmark_history = {}  # Store landmark history for each hand ID
#         self.history_size = 5       # Number of frames to keep in history
#         self.smoothing_factor = 0.7 # Weight for current landmarks vs history (0-1)
#         self.min_tracking_confidence = 0.3  # Minimum confidence to keep tracking
#         self.last_landmarks = None  # Store last valid landmarks
#         self.frames_without_detection = 0
#         self.max_lost_frames = 10  

#     def start(self):
#         """Start the camera capture thread"""
#         if self.is_running:
#             print("Camera is already running")
#             return
        
#         # Initialize video capture
#         self.cap = cv2.VideoCapture(self.camera_id)
#         self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
#         self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
#         if not self.cap.isOpened():
#             raise RuntimeError(f"Failed to open camera with ID {self.camera_id}")
        
#         # Start the capture thread
#         self.is_running = True
#         self.thread = threading.Thread(target=self._capture_loop)
#         self.thread.daemon = True
#         self.thread.start()
#         print(f"Camera started with ID {self.camera_id}")
        
#     # def _capture_loop(self):
#     #     """Main capture loop that runs in a separate thread"""
#     #     while self.is_running:
#     #         # Read a new frame from the video stream
#     #         ret, frame = self.cap.read()
            
#     #         if not ret:
#     #             print("Failed to capture frame")
#     #             time.sleep(0.1)
#     #             continue
            
#     #         # Mirror the frame if enabled
#     #         if self.mirror:
#     #             frame = cv2.flip(frame, 1)
            
#     #         # Calculate FPS
#     #         self.new_frame_time = time.time()
#     #         self.fps = 1 / (self.new_frame_time - self.prev_frame_time) if self.prev_frame_time > 0 else 0
#     #         self.prev_frame_time = self.new_frame_time
            
#     #         # Process the frame with MediaPipe
#     #         processed = self._process_frame(frame.copy())
            
#     #         # Thread-safe update of the current frame
#     #         with self.lock:
#     #             self.frame = frame.copy()
#     #             self.processed_frame = processed
            
#     #         # Slight sleep to reduce CPU usage
#     #         time.sleep(0.01)

#     def _capture_loop(self):
#         """Main capture loop that runs in a separate thread"""
#         frame_count = 0
        
#         while self.is_running:
#             # Read a new frame from the video stream
#             ret, frame = self.cap.read()
            
#             if not ret:
#                 print("Failed to capture frame")
#                 time.sleep(0.1)
#                 continue
            
#             # Mirror the frame if enabled
#             if self.mirror:
#                 frame = cv2.flip(frame, 1)
            
#             # Calculate FPS
#             self.new_frame_time = time.time()
#             self.fps = 1 / (self.new_frame_time - self.prev_frame_time) if self.prev_frame_time > 0 else 0
#             self.prev_frame_time = self.new_frame_time
            
#             # Determine if we should log this frame (every 5 frames to avoid excessive logs)
#             log_this_frame = (frame_count % 5 == 0)
#             frame_count += 1
            
#             # Process the frame with MediaPipe
#             processed = self._process_frame(frame.copy(), log_landmarks=log_this_frame)
            
#             # Thread-safe update of the current frame
#             with self.lock:
#                 self.frame = frame.copy()
#                 self.processed_frame = processed
            
#             # Slight sleep to reduce CPU usage
#             time.sleep(0.01)
#     # def _process_frame(self, frame):
#     #     """Process frame to detect hands and draw landmarks"""
#     #     # Convert BGR to RGB for MediaPipe (MediaPipe requires RGB input)
#     #     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#     #     # Process the RGB frame with MediaPipe
#     #     results = self.hands.process(rgb_frame)
        
#     #     # Store the hand landmarks data for external use
#     #     self.hand_landmarks_data = results.multi_hand_landmarks
        
#     #     # Create a copy of the frame to draw on
#     #     annotated_frame = frame.copy()
        
#     #     # Draw FPS information
#     #     cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30), 
#     #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
#     #     # Draw hand landmarks if enabled
#     #     if self.show_landmarks and results.multi_hand_landmarks:
#     #         for hand_landmarks in results.multi_hand_landmarks:
#     #             # Draw the hand landmarks
#     #             self.mp_drawing.draw_landmarks(
#     #                 annotated_frame,
#     #                 hand_landmarks,
#     #                 self.mp_hands.HAND_CONNECTIONS,
#     #                 self.mp_drawing_styles.get_default_hand_landmarks_style(),
#     #                 self.mp_drawing_styles.get_default_hand_connections_style()
#     #             )
        
#     #     # Return the processed frame with annotations
#     #     return annotated_frame
    
#     def get_frame(self, processed=True):
#         """Return the current frame (processed or raw)"""
#         with self.lock:
#             if processed and self.processed_frame is not None:
#                 return self.processed_frame.copy()
#             elif self.frame is not None:
#                 return self.frame.copy()
#             return None
    
#     def get_jpeg_frame(self, processed=True):
#         """Return JPEG encoded frame for web streaming"""
#         frame = self.get_frame(processed)
#         if frame is None:
#             # Return a blank frame if no frame is available
#             blank = np.zeros((self.height, self.width, 3), np.uint8)
#             _, jpeg = cv2.imencode('.jpg', blank)
#             return jpeg.tobytes()
        
#         _, jpeg = cv2.imencode('.jpg', frame)
#         return jpeg.tobytes()
    
#     def get_hand_landmarks(self):
#         """Return the current hand landmarks data"""
#         return self.hand_landmarks_data
    
#     def stop(self):
#         """Stop the camera and release resources"""
#         self.is_running = False
#         if self.thread:
#             self.thread.join(timeout=1.0)
#             self.thread = None
        
#         if hasattr(self, 'cap') and self.cap:
#             self.cap.release()

#     # def _process_frame(self, frame):
#     #     """
#     #     Process frame to detect hands and extract landmarks
        
#     #     Steps:
#     #     1. Convert BGR to RGB for MediaPipe
#     #     2. Pass the RGB frame to the Hands detection module
#     #     3. Extract landmark coordinates if hands are detected
#     #     4. Analyze the hand position and orientation
#     #     5. Visualize the results on the frame
#     #     """
#     #     # Step 1: Convert BGR to RGB for MediaPipe (MediaPipe requires RGB input)
#     #     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#     #     # Step 2: Process the RGB frame with MediaPipe Hands
#     #     results = self.hands.process(rgb_frame)
        
#     #     # Create a copy of the frame to draw on
#     #     annotated_frame = frame.copy()
        
#     #     # Draw FPS information
#     #     cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30), 
#     #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
#     #     # Step 3: Extract landmark coordinates if hands are detected
#     #     if results.multi_hand_landmarks:
#     #         # Store the hand landmarks data for external use
#     #         self.hand_landmarks_data = results.multi_hand_landmarks
            
#     #         # Process each detected hand
#     #         for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
#     #             # Extract hand classification (Left/Right) if available
#     #             hand_label = "Hand"
#     #             if results.multi_handedness and len(results.multi_handedness) > hand_idx:
#     #                 hand_classification = results.multi_handedness[hand_idx]
#     #                 hand_label = f"{hand_classification.classification[0].label} Hand"
#     #                 confidence = hand_classification.classification[0].score
#     #                 hand_label = f"{hand_label} ({confidence:.2f})"
                
#     #             # Draw the appropriate label
#     #             wrist_landmark = hand_landmarks.landmark[0]  # Wrist landmark
#     #             x, y = int(wrist_landmark.x * frame.shape[1]), int(wrist_landmark.y * frame.shape[0])
#     #             cv2.putText(annotated_frame, hand_label, (x - 10, y - 10), 
#     #                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                
#     #             # Step 4: Extract and analyze landmarks
#     #             self._analyze_hand_landmarks(hand_landmarks, hand_idx)
                
#     #             # Step 5: Draw the hand landmarks on the frame
#     #             self.mp_drawing.draw_landmarks(
#     #                 annotated_frame,
#     #                 hand_landmarks,
#     #                 self.mp_hands.HAND_CONNECTIONS,
#     #                 self.mp_drawing_styles.get_default_hand_landmarks_style(),
#     #                 self.mp_drawing_styles.get_default_hand_connections_style()
#     #             )
#     #     else:
#     #         # No hands detected
#     #         self.hand_landmarks_data = None
#     #         cv2.putText(annotated_frame, "No hands detected", (10, 60), 
#     #                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
#     #     # Return the processed frame with annotations
#     #     return annotated_frame

#     # def _process_frame(self, frame):
#     #     """Process frame to detect hands and draw landmarks"""
#     #     # Convert BGR to RGB for MediaPipe (MediaPipe requires RGB input)
#     #     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#     #     # Process the RGB frame with MediaPipe
#     #     results = self.hands.process(rgb_frame)
        
#     #     # Create a copy of the frame to draw on
#     #     annotated_frame = frame.copy()
        
#     #     # Draw FPS information
#     #     cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30), 
#     #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
#     #     # Store the hand landmarks data for external use
#     #     self.hand_landmarks_data = results.multi_hand_landmarks
        
#     #     # Draw hand landmarks if enabled
#     #     if self.show_landmarks and results.multi_hand_landmarks:
#     #         for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
#     #             # Draw the hand landmarks
#     #             self.mp_drawing.draw_landmarks(
#     #                 annotated_frame,
#     #                 hand_landmarks,
#     #                 self.mp_hands.HAND_CONNECTIONS,
#     #                 self.mp_drawing_styles.get_default_hand_landmarks_style(),
#     #                 self.mp_drawing_styles.get_default_hand_connections_style()
#     #             )
                
#     #             # Extract and log key landmarks
#     #             key_landmarks = self.extract_key_landmarks(hand_landmarks, annotated_frame.shape)
                
#     #             # Visualize the key landmarks with different colors
#     #             # Wrist - Red
#     #             cv2.circle(annotated_frame, key_landmarks['wrist']['pixel'], 8, (0, 0, 255), -1)
                
#     #             # Thumb Tip - Green
#     #             cv2.circle(annotated_frame, key_landmarks['thumb_tip']['pixel'], 8, (0, 255, 0), -1)
                
#     #             # Index Tip - Blue
#     #             cv2.circle(annotated_frame, key_landmarks['index_tip']['pixel'], 8, (255, 0, 0), -1)
                
#     #             # Add coordinate labels
#     #             for landmark_name in ['wrist', 'thumb_tip', 'index_tip']:
#     #                 pixel_coord = key_landmarks[landmark_name]['pixel']
#     #                 coordinate_text = f"{landmark_name}: ({pixel_coord[0]},{pixel_coord[1]})"
#     #                 y_offset = 20 if landmark_name == 'wrist' else (40 if landmark_name == 'thumb_tip' else 60)
#     #                 cv2.putText(
#     #                     annotated_frame,
#     #                     coordinate_text,
#     #                     (10, annotated_frame.shape[0] - y_offset), 
#     #                     cv2.FONT_HERSHEY_SIMPLEX,
#     #                     0.5,
#     #                     (255, 255, 255),
#     #                     1
#     #                 )
        
#     #     # Return the processed frame with annotations
#     #     return annotated_frame

#     def _process_frame(self, frame, log_landmarks=False):
#         """
#         Process frame to detect hands and draw landmarks
        
#         Args:
#             frame: The frame to process
#             log_landmarks: Whether to log landmark coordinates
#         """
#         # Convert BGR to RGB for MediaPipe (MediaPipe requires RGB input)
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
#         # Process the RGB frame with MediaPipe
#         results = self.hands.process(rgb_frame)
        
#         # Create a copy of the frame to draw on
#         annotated_frame = frame.copy()
        
#         # Draw FPS information
#         cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30), 
#                     cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
#         # Store the hand landmarks data for external use
#         self.hand_landmarks_data = results.multi_hand_landmarks
        
#         # Draw hand landmarks if enabled
#         if self.show_landmarks and results.multi_hand_landmarks:
#             for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
#                 # Draw the hand landmarks
#                 self.mp_drawing.draw_landmarks(
#                     annotated_frame,
#                     hand_landmarks,
#                     self.mp_hands.HAND_CONNECTIONS,
#                     self.mp_drawing_styles.get_default_hand_landmarks_style(),
#                     self.mp_drawing_styles.get_default_hand_connections_style()
#                 )
                
#                 # Extract and log key landmarks
#                 key_landmarks = self.extract_key_landmarks(
#                     hand_landmarks, 
#                     annotated_frame.shape,
#                     log_to_csv=log_landmarks
#                 )
                
#                 # Visualize the key landmarks with different colors
#                 # Wrist - Red
#                 cv2.circle(annotated_frame, key_landmarks['wrist']['pixel'], 8, (0, 0, 255), -1)
                
#                 # Thumb Tip - Green
#                 cv2.circle(annotated_frame, key_landmarks['thumb_tip']['pixel'], 8, (0, 255, 0), -1)
                
#                 # Index Tip - Blue
#                 cv2.circle(annotated_frame, key_landmarks['index_tip']['pixel'], 8, (255, 0, 0), -1)
                
#                 # Add coordinate labels if logging
#                 if log_landmarks:
#                     for landmark_name in ['wrist', 'thumb_tip', 'index_tip']:
#                         pixel_coord = key_landmarks[landmark_name]['pixel']
#                         normalized_coord = key_landmarks[landmark_name]['normalized']
#                         coordinate_text = f"{landmark_name}: ({normalized_coord[0]:.2f},{normalized_coord[1]:.2f},{normalized_coord[2]:.2f})"
#                         y_offset = 20 if landmark_name == 'wrist' else (40 if landmark_name == 'thumb_tip' else 60)
#                         cv2.putText(
#                             annotated_frame,
#                             coordinate_text,
#                             (10, annotated_frame.shape[0] - y_offset), 
#                             cv2.FONT_HERSHEY_SIMPLEX,
#                             0.5,
#                             (255, 255, 255),
#                             1
#                         )
        
#         # Return the processed frame with annotations
#         return annotated_frame
  
#     def _analyze_hand_landmarks(self, hand_landmarks, hand_idx=0):
#         """
#         Analyze hand landmarks for tracking and gesture recognition
        
#         Args:
#             hand_landmarks: MediaPipe hand landmarks
#             hand_idx: Index of the hand if multiple hands are detected
#         """
#         # Create a structured representation of the landmarks
#         landmarks_array = []
        
#         # Extract 3D coordinates for all 21 landmarks
#         for idx, landmark in enumerate(hand_landmarks.landmark):
#             # Convert normalized coordinates to pixel values for the frame
#             landmarks_array.append({
#                 'id': idx,
#                 'x': landmark.x,  # Normalized X (0.0 to 1.0)
#                 'y': landmark.y,  # Normalized Y (0.0 to 1.0)
#                 'z': landmark.z,  # Normalized Z (depth)
#                 'name': self._get_landmark_name(idx)
#             })
        
#         # Calculate key metrics for hand analysis
        
#         # 1. Hand openness (distance between thumb tip and pinky tip)
#         thumb_tip = hand_landmarks.landmark[4]
#         pinky_tip = hand_landmarks.landmark[20]
#         hand_openness = self._calculate_distance(thumb_tip, pinky_tip)
        
#         # 2. Hand orientation (wrist to middle finger MCP vector)
#         wrist = hand_landmarks.landmark[0]
#         middle_mcp = hand_landmarks.landmark[9]
#         hand_orientation = (middle_mcp.x - wrist.x, middle_mcp.y - wrist.y)
        
#         # Store the analysis results for this hand
#         hand_analysis = {
#             'hand_idx': hand_idx,
#             'landmarks': landmarks_array,
#             'hand_openness': hand_openness,
#             'hand_orientation': hand_orientation
#         }
        
#         # Store the analysis for external access
#         # This can be used by gesture recognition and other modules
#         if not hasattr(self, 'hand_analysis_data'):
#             self.hand_analysis_data = []
        
#         # Update or add this hand's analysis
#         if len(self.hand_analysis_data) <= hand_idx:
#             self.hand_analysis_data.append(hand_analysis)
#         else:
#             self.hand_analysis_data[hand_idx] = hand_analysis
        
#         return hand_analysis

#     def _calculate_distance(self, landmark1, landmark2):
#         """Calculate 3D distance between two landmarks"""
#         return ((landmark1.x - landmark2.x) ** 2 + 
#                 (landmark1.y - landmark2.y) ** 2 + 
#                 (landmark1.z - landmark2.z) ** 2) ** 0.5

#     def _get_landmark_name(self, idx):
#         """Get the anatomical name of a landmark by its index"""
#         landmark_names = [
#             "WRIST",
#             "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
#             "INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP",
#             "MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP",
#             "RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP",
#             "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP"
#         ]
#         return landmark_names[idx] if 0 <= idx < len(landmark_names) else f"UNKNOWN_{idx}"

#     def get_hand_analysis(self):
#         """Return the current hand analysis data for external use"""
#         if hasattr(self, 'hand_analysis_data'):
#             return self.hand_analysis_data
#         return None

#     def get_landmark_coordinates(self, hand_idx=0):

#         """
#         Get the landmark coordinates for a specific hand
        
#         Returns:
#             dict: Dictionary of landmark coordinates with keys:
#                 - 'wrist': (x, y) of wrist
#                 - 'thumb_tip': (x, y) of thumb tip
#                 - 'index_tip': (x, y) of index finger tip
#                 - 'middle_tip': (x, y) of middle finger tip
#                 - 'ring_tip': (x, y) of ring finger tip
#                 - 'pinky_tip': (x, y) of pinky tip
#         """
#         if not self.hand_landmarks_data or hand_idx >= len(self.hand_landmarks_data):
#             return None
        
#         hand_landmarks = self.hand_landmarks_data[hand_idx]
        
#         # Get current frame size for converting normalized coordinates to pixels
#         frame = self.get_frame(processed=False)
#         if frame is None:
#             return None
        
#         height, width = frame.shape[:2]
        
#         # Extract key landmarks
#         wrist = hand_landmarks.landmark[0]
#         thumb_tip = hand_landmarks.landmark[4]
#         index_tip = hand_landmarks.landmark[8]
#         middle_tip = hand_landmarks.landmark[12]
#         ring_tip = hand_landmarks.landmark[16]
#         pinky_tip = hand_landmarks.landmark[20]
        
#         # Convert normalized coordinates to pixel coordinates
#         return {
#             'wrist': (int(wrist.x * width), int(wrist.y * height)),
#             'thumb_tip': (int(thumb_tip.x * width), int(thumb_tip.y * height)),
#             'index_tip': (int(index_tip.x * width), int(index_tip.y * height)),
#             'middle_tip': (int(middle_tip.x * width), int(middle_tip.y * height)),
#             'ring_tip': (int(ring_tip.x * width), int(ring_tip.y * height)),
#             'pinky_tip': (int(pinky_tip.x * width), int(pinky_tip.y * height))
#         }

#     # def extract_key_landmarks(self, hand_landmarks, frame_shape):

#     #     """
#     #     Extract and log coordinates of key hand landmarks.
        
#     #     Args:
#     #         hand_landmarks: MediaPipe hand landmarks
#     #         frame_shape: Frame dimensions (height, width)
        
#     #     Returns:
#     #         dict: Coordinates of key landmarks
#     #     """
#     #     height, width = frame_shape[:2]
        
#     #     # Extract the three key landmarks
#     #     wrist = hand_landmarks.landmark[0]
#     #     thumb_tip = hand_landmarks.landmark[4]
#     #     index_tip = hand_landmarks.landmark[8]
        
#     #     # Convert normalized coordinates to pixel coordinates (for visualization)
#     #     wrist_px = (int(wrist.x * width), int(wrist.y * height))
#     #     thumb_tip_px = (int(thumb_tip.x * width), int(thumb_tip.y * height))
#     #     index_tip_px = (int(index_tip.x * width), int(index_tip.y * height))
        
#     #     # Create a dictionary with both normalized and pixel coordinates
#     #     key_landmarks = {
#     #         'wrist': {
#     #             'normalized': (wrist.x, wrist.y, wrist.z),
#     #             'pixel': wrist_px
#     #         },
#     #         'thumb_tip': {
#     #             'normalized': (thumb_tip.x, thumb_tip.y, thumb_tip.z),
#     #             'pixel': thumb_tip_px
#     #         },
#     #         'index_tip': {
#     #             'normalized': (index_tip.x, index_tip.y, index_tip.z),
#     #             'pixel': index_tip_px
#     #         }
#     #     }
        
#     #     # Log the coordinates
#     #     print(f"Key Landmark Coordinates:")
#     #     print(f"  Wrist:      {key_landmarks['wrist']['normalized']} (normalized), {key_landmarks['wrist']['pixel']} (pixels)")
#     #     print(f"  Thumb Tip:  {key_landmarks['thumb_tip']['normalized']} (normalized), {key_landmarks['thumb_tip']['pixel']} (pixels)")
#     #     print(f"  Index Tip:  {key_landmarks['index_tip']['normalized']} (normalized), {key_landmarks['index_tip']['pixel']} (pixels)")
        
#     #     return key_landmarks
    
#     def extract_key_landmarks(self, hand_landmarks, frame_shape, log_to_csv=True):
#         """
#         Extract and log coordinates of key hand landmarks.
        
#         Args:
#             hand_landmarks: MediaPipe hand landmarks
#             frame_shape: Frame dimensions (height, width)
#             log_to_csv: Whether to log coordinates to CSV file
        
#         Returns:
#             dict: Coordinates of key landmarks
#         """
#         height, width = frame_shape[:2]
        
#         # Extract the three key landmarks
#         wrist = hand_landmarks.landmark[0]
#         thumb_tip = hand_landmarks.landmark[4]
#         index_tip = hand_landmarks.landmark[8]
        
#         # Convert normalized coordinates to pixel coordinates (for visualization)
#         wrist_px = (int(wrist.x * width), int(wrist.y * height))
#         thumb_tip_px = (int(thumb_tip.x * width), int(thumb_tip.y * height))
#         index_tip_px = (int(index_tip.x * width), int(index_tip.y * height))
        
#         # Create a dictionary with both normalized and pixel coordinates
#         key_landmarks = {
#             'wrist': {
#                 'normalized': (wrist.x, wrist.y, wrist.z),
#                 'pixel': wrist_px
#             },
#             'thumb_tip': {
#                 'normalized': (thumb_tip.x, thumb_tip.y, thumb_tip.z),
#                 'pixel': thumb_tip_px
#             },
#             'index_tip': {
#                 'normalized': (index_tip.x, index_tip.y, index_tip.z),
#                 'pixel': index_tip_px
#             }
#         }
        
#         # Log the coordinates to console
#         print(f"Key Landmark Coordinates:")
#         print(f"  Wrist:      {key_landmarks['wrist']['normalized']} (normalized), {key_landmarks['wrist']['pixel']} (pixels)")
#         print(f"  Thumb Tip:  {key_landmarks['thumb_tip']['normalized']} (normalized), {key_landmarks['thumb_tip']['pixel']} (pixels)")
#         print(f"  Index Tip:  {key_landmarks['index_tip']['normalized']} (normalized), {key_landmarks['index_tip']['pixel']} (pixels)")
        
#         # Log to CSV if requested
#         if log_to_csv:
#             self.log_landmarks_to_csv(key_landmarks)
        
#         return key_landmarks

#     def log_landmarks_to_csv(self, key_landmarks, timestamp=None):

#         """
#         Log the landmark coordinates to a CSV file
        
#         Args:
#             key_landmarks: Dictionary of key landmarks
#             timestamp: Optional timestamp (defaults to current time)
#         """
#         import csv
#         import os
#         from datetime import datetime
        
#         timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        
#         # Create logs directory if it doesn't exist
#         if not os.path.exists('logs'):
#             os.makedirs('logs')
        
#         # Create or append to CSV file
#         csv_file = 'logs/hand_landmarks.csv'
#         file_exists = os.path.isfile(csv_file)
        
#         with open(csv_file, mode='a', newline='') as file:
#             fieldnames = ['timestamp', 
#                         'wrist_x', 'wrist_y', 'wrist_z',
#                         'thumb_tip_x', 'thumb_tip_y', 'thumb_tip_z',
#                         'index_tip_x', 'index_tip_y', 'index_tip_z']
            
#             writer = csv.DictWriter(file, fieldnames=fieldnames)
            
#             # Write header if file is new
#             if not file_exists:
#                 writer.writeheader()
            
#             # Write the landmark coordinates
#             writer.writerow({
#                 'timestamp': timestamp,
#                 'wrist_x': key_landmarks['wrist']['normalized'][0],
#                 'wrist_y': key_landmarks['wrist']['normalized'][1],
#                 'wrist_z': key_landmarks['wrist']['normalized'][2],
#                 'thumb_tip_x': key_landmarks['thumb_tip']['normalized'][0],
#                 'thumb_tip_y': key_landmarks['thumb_tip']['normalized'][1],
#                 'thumb_tip_z': key_landmarks['thumb_tip']['normalized'][2],
#                 'index_tip_x': key_landmarks['index_tip']['normalized'][0],
#                 'index_tip_y': key_landmarks['index_tip']['normalized'][1],
#                 'index_tip_z': key_landmarks['index_tip']['normalized'][2]
#             })
   
#     def _smooth_landmarks(self, current_landmarks, hand_id=0):
#         """
#         Apply temporal smoothing to reduce jitter in landmark positions
        
#         Args:
#             current_landmarks: Current frame's hand landmarks
#             hand_id: ID to track multiple hands separately
            
#         Returns:
#             Smoothed landmarks object
#         """
#         # Initialize history for this hand if it doesn't exist
#         if hand_id not in self.landmark_history:
#             self.landmark_history[hand_id] = []
        
#         # Create a copy of the landmarks for smoothing
#         smoothed_landmarks = copy.deepcopy(current_landmarks)
        
#         # Add current landmarks to history
#         self.landmark_history[hand_id].append(current_landmarks)
        
#         # Keep history at designated size
#         if len(self.landmark_history[hand_id]) > self.history_size:
#             self.landmark_history[hand_id].pop(0)
        
#         # Apply exponential moving average if we have history
#         if len(self.landmark_history[hand_id]) > 1:
#             # Get the history for this hand
#             history = self.landmark_history[hand_id]
            
#             # For each landmark point
#             for i in range(len(current_landmarks.landmark)):
#                 # Start with current position
#                 x = current_landmarks.landmark[i].x * self.smoothing_factor
#                 y = current_landmarks.landmark[i].y * self.smoothing_factor
#                 z = current_landmarks.landmark[i].z * self.smoothing_factor
                
#                 # Add weighted contributions from history (more recent = higher weight)
#                 weight_sum = self.smoothing_factor
#                 for j in range(len(history) - 1):
#                     # Calculate weight (decreasing for older frames)
#                     weight = (1.0 - self.smoothing_factor) * (j + 1) / len(history)
#                     x += history[j].landmark[i].x * weight
#                     y += history[j].landmark[i].y * weight
#                     z += history[j].landmark[i].z * weight
#                     weight_sum += weight
                
#                 # Normalize by weight sum
#                 if weight_sum > 0:
#                     smoothed_landmarks.landmark[i].x = x / weight_sum
#                     smoothed_landmarks.landmark[i].y = y / weight_sum
#                     smoothed_landmarks.landmark[i].z = z / weight_sum
        
#         return smoothed_landmarks

#     def _is_valid_movement(self, current_landmarks, previous_landmarks, max_velocity=0.3):
#         """
#         Check if movement between frames is realistic or an outlier
        
#         Args:
#             current_landmarks: Current detected landmarks
#             previous_landmarks: Previous frame's landmarks
#             max_velocity: Maximum allowed normalized velocity between frames
            
#         Returns:
#             Boolean: True if movement is valid, False if likely an outlier
#         """
#         if not previous_landmarks:
#             return True  # No previous data to compare
        
#         # Check key landmarks (wrist and fingertips)
#         key_indices = [0, 4, 8, 12, 16, 20]  # Wrist and fingertips
        
#         for idx in key_indices:
#             curr = current_landmarks.landmark[idx]
#             prev = previous_landmarks.landmark[idx]
            
#             # Calculate velocity (change in position)
#             velocity = math.sqrt(
#                 (curr.x - prev.x)**2 + 
#                 (curr.y - prev.y)**2 + 
#                 (curr.z - prev.z)**2
#             )
            
#             if velocity > max_velocity:
#                 return False  # Movement too fast, likely an outlier
        
#         return True  # Movement is valid

#     def _visualize_key_landmarks(self, frame, key_landmarks):

#         """Highlight and label the key landmarks on the frame"""
#         # Draw wrist point (red)
#         cv2.circle(frame, key_landmarks['wrist']['pixel'], 8, (0, 0, 255), -1)
        
#         # Draw thumb tip (green)
#         cv2.circle(frame, key_landmarks['thumb_tip']['pixel'], 8, (0, 255, 0), -1)
        
#         # Draw index tip (blue)
#         cv2.circle(frame, key_landmarks['index_tip']['pixel'], 8, (255, 0, 0), -1)
        
#         # Draw connecting lines for better visualization
#         cv2.line(frame, key_landmarks['wrist']['pixel'], 
#                 key_landmarks['thumb_tip']['pixel'], (0, 255, 255), 2)
#         cv2.line(frame, key_landmarks['wrist']['pixel'], 
#                 key_landmarks['index_tip']['pixel'], (255, 0, 255), 2)


# import copy

# class LandmarkSmoother:
#     def __init__(self, smoothing_factor=0.3, history_size=5):
#         """
#         Initialize the landmark smoother
        
#         Args:
#             smoothing_factor: Weight for new values vs. previous values (0-1)
#                               Lower values create more smoothing but more lag
#             history_size: Number of frames to keep in history for advanced filtering
#         """
#         self.smoothing_factor = smoothing_factor
#         self.history_size = history_size
#         self.landmark_history = []
#         self.prev_landmarks = None
#         self.lost_frames = 0
    
#     def update(self, new_landmarks):
#         """
#         Update the smoothed landmarks with new detected landmarks
        
#         Args:
#             new_landmarks: New MediaPipe hand landmarks, or None if not detected
            
#         Returns:
#             Smoothed landmarks or None if landmarks can't be predicted
#         """
#         # If no landmarks detected
#         if new_landmarks is None:
#             self.lost_frames += 1
#             # If we have previous landmarks, try to predict current position
#             if self.prev_landmarks and self.lost_frames < 5:
#                 return self.prev_landmarks
#             # If lost for too many frames, can't predict
#             return None
        
#         # Reset lost frame counter
#         self.lost_frames = 0
        
#         # Initialize first landmarks
#         if self.prev_landmarks is None:
#             self.prev_landmarks = self._copy_landmarks(new_landmarks)
#             return new_landmarks
        
#         # Add to history
#         self.landmark_history.append(self._extract_landmark_positions(new_landmarks))
#         if len(self.landmark_history) > self.history_size:
#             self.landmark_history.pop(0)
        
#         # Apply smoothing filter
#         smoothed = self._apply_smoothing(new_landmarks)
#         self.prev_landmarks = smoothed
        
#         return smoothed
    
#     def _copy_landmarks(self, landmarks):
#         """Create a deep copy of landmarks to avoid modifying the original"""
#         return copy.deepcopy(landmarks)
    
#     def _extract_landmark_positions(self, landmarks):
#         """Extract positions from landmarks for history tracking"""
#         positions = []
#         for landmark in landmarks.landmark:
#             positions.append((landmark.x, landmark.y, landmark.z))
#         return positions
    
#     def _apply_smoothing(self, new_landmarks):
#         """Apply smoothing to landmarks"""
#         result = self._copy_landmarks(new_landmarks)
        
#         # Apply exponential smoothing to each landmark
#         for i, landmark in enumerate(new_landmarks.landmark):
#             result.landmark[i].x = (self.smoothing_factor * landmark.x + 
#                                   (1 - self.smoothing_factor) * self.prev_landmarks.landmark[i].x)
#             result.landmark[i].y = (self.smoothing_factor * landmark.y + 
#                                   (1 - self.smoothing_factor) * self.prev_landmarks.landmark[i].y)
#             result.landmark[i].z = (self.smoothing_factor * landmark.z + 
#                                   (1 - self.smoothing_factor) * self.prev_landmarks.landmark[i].z)
        
#         return result

import collections
import numpy as np
import cv2
import mediapipe as mp
import time
import threading
from gesture_tracking import HandLandmarkTracker
from gesture_detector import SelectionGestureDetector
class LandmarkBuffer:
    """
    Maintains a time-sequenced buffer of hand landmark coordinates
    from the last 10 frames for gesture motion analysis.
    """
    
    def __init__(self, max_frames=10):
        """
        Initialize the landmark buffer with specified capacity.
        
        Args:
            max_frames: Maximum number of frames to store in the buffer (default: 10)
        """
        self.max_frames = max_frames
        # Using deque for efficient rolling buffer implementation
        self.frames = collections.deque(maxlen=max_frames)
        self.timestamps = collections.deque(maxlen=max_frames)
        self.lock = threading.Lock()  # Reuse existing threading module
    
    def add_frame(self, landmarks, timestamp=None):
        """
        Add landmark data from a new frame to the buffer.
        
        Args:
            landmarks: List of hand landmarks from MediaPipe
            timestamp: Timestamp of the frame (defaults to current time if None)
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Convert and extract landmark coordinates
        frame_data = self._extract_landmarks(landmarks)
        
        # Thread-safe update of the buffer
        with self.lock:
            self.frames.append(frame_data)
            self.timestamps.append(timestamp)
    
    def _extract_landmarks(self, multi_hand_landmarks):
        """
        Extract and convert MediaPipe hand landmarks to a structured format.
        
        Args:
            multi_hand_landmarks: MediaPipe hand landmarks result
            
        Returns:
            Structured array of landmark coordinates for each detected hand
        """
        if not multi_hand_landmarks:
            return []
            
        frame_data = []
        
        for hand_idx, hand_landmarks in enumerate(multi_hand_landmarks):
            # Each hand has 21 landmarks
            hand_data = np.zeros((21, 3), dtype=np.float32)
            
            # Extract x, y, z coordinates for each landmark
            for i, landmark in enumerate(hand_landmarks.landmark):
                hand_data[i, 0] = landmark.x  # x coordinate
                hand_data[i, 1] = landmark.y  # y coordinate
                hand_data[i, 2] = landmark.z  # z coordinate
                
            frame_data.append(hand_data)
            
        return frame_data
    
    def get_buffer(self):
        """
        Get the entire buffer with timestamps.
        
        Returns:
            List of (landmarks, timestamp) pairs, oldest first
        """
        with self.lock:
            # Create a copy of the data to avoid external modifications
            return list(zip(list(self.frames), list(self.timestamps)))
    
    def get_landmark_sequence(self, hand_idx=0, landmark_idx=8):
        """
        Get the sequence of a specific landmark across all buffered frames.
        Default is index fingertip (landmark 8) of the first hand.
        
        Args:
            hand_idx: Hand index (0 for first hand, 1 for second hand if present)
            landmark_idx: Landmark index (0-20, according to MediaPipe hand model)
            
        Returns:
            Numpy array of shape (n, 3) where n is the number of frames
            containing that landmark, and 3 represents (x, y, z) coordinates,
            and corresponding timestamps array
        """
        with self.lock:
            sequence = []
            frame_times = []
            
            for idx, (frame_data, timestamp) in enumerate(zip(self.frames, self.timestamps)):
                # Skip frames where the specified hand is not detected
                if not frame_data or hand_idx >= len(frame_data):
                    continue
                
                # Get the specified landmark coordinates
                hand_data = frame_data[hand_idx]
                if landmark_idx < len(hand_data):
                    sequence.append(hand_data[landmark_idx])
                    frame_times.append(timestamp)
            
            # Return as numpy arrays for easier processing
            return np.array(sequence), np.array(frame_times)
    
    def clear(self):
        """Clear the buffer"""
        with self.lock:
            self.frames.clear()
            self.timestamps.clear()

    def get_fingertips_sequence(self, hand_idx=0):
        """
        Get the trajectory of all fingertips (thumb, index, middle, ring, pinky) 
        across buffered frames.
        
        Args:
            hand_idx: Hand index (0 for first hand, 1 for second hand if present)
            
        Returns:
            Dictionary of fingertip trajectories and timestamps
        """
        # Fingertip landmark indices in MediaPipe hand model
        fingertip_indices = {
            'thumb': 4,
            'index': 8,
            'middle': 12,
            'ring': 16,
            'pinky': 20
        }
        
        result = {}
        with self.lock:
            for finger_name, landmark_idx in fingertip_indices.items():
                points = []
                frame_times = []
                
                for idx, (frame_data, timestamp) in enumerate(zip(self.frames, self.timestamps)):
                    # Skip frames where the specified hand is not detected
                    if not frame_data or hand_idx >= len(frame_data):
                        continue
                    
                    # Get the specified landmark coordinates
                    hand_data = frame_data[hand_idx]
                    if landmark_idx < len(hand_data):
                        points.append(hand_data[landmark_idx])
                        frame_times.append(timestamp)
                
                # Store as numpy arrays
                if points:
                    result[finger_name] = {
                        'points': np.array(points),
                        'timestamps': np.array(frame_times)
                    }
                else:
                    result[finger_name] = {'points': np.array([]), 'timestamps': np.array([])}
        
        return result

# Update the existing Camera class in camera.py
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
        
        # Initialize landmark buffer for motion tracking - NEW ADDITION
        self.landmark_buffer = LandmarkBuffer(max_frames=10)
        # Gesture tracking setup
        self.landmark_tracker = HandLandmarkTracker(buffer_size=10, min_gesture_duration_ms=500)
        # Gesture state tracking
        self.raw_gesture = None        # From your existing gesture recognizer
        self.validated_gesture = None  # For validated static gestures
        
        self.raw_motion = None         # Detected motion (unvalidated)
        self.validated_motion = None   # Validated motion gesture
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.7    # Seconds between gesture recognition
        
        # Motion detection parameters
        self.motion_threshold = 0.12       # Min velocity for motion detection
        self.confidence_threshold = 0.6    # Directional confidence threshold
        
        # Debug visualization
        self.show_validation_status = False
        
        # Add selection gesture detector
        self.selection_detector = SelectionGestureDetector(cooldown_period=1.0)
        self.current_selection_gesture = None

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
    
    # def _process_frame(self, frame):
    #     """Process frame to detect hands and draw landmarks"""
    #     # Convert BGR to RGB for MediaPipe (MediaPipe requires RGB input)
    #     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
    #     # Process the RGB frame with MediaPipe
    #     results = self.hands.process(rgb_frame)
        
    #     current_time = time.time()
        
    #     # Process gestures if hands are detected
    #     if results.multi_hand_landmarks and len(results.multi_hand_landmarks) > 0:
    #         # Add landmarks to the tracker
    #         self.landmark_tracker.add_landmarks(results.multi_hand_landmarks)
            
    #         # Get the primary hand landmarks
    #         primary_hand_landmarks = results.multi_hand_landmarks[0].landmark
            
    #         # Static gesture processing (using your existing gesture recognizer)
    #         # This code depends on your existing implementation...
            
    #         # Motion gesture processing with validation
    #         if current_time - self.last_gesture_time > self.gesture_cooldown:
    #             # Detect and validate motion gestures
    #             motion, is_validated = self.landmark_tracker.detect_motion_gesture(
    #                 landmarks=primary_hand_landmarks,
    #                 threshold=self.motion_threshold,
    #                 confidence_threshold=self.confidence_threshold,
    #                 current_time=current_time
    #             )
                
    #             # Update gesture state
    #             if motion not in ['stationary', 'insufficient_data', 'invalid_posture']:
    #                 self.raw_motion = motion
                    
    #                 # Store validated gesture
    #                 if is_validated:
    #                     self.validated_motion = motion
    #                     self.last_gesture_time = current_time
    #                     self.logger.info(f"Validated motion gesture: {motion}")
        
    #     # Show validation debug info if enabled
    #     if self.show_validation_status and frame is not None:
    #         self._draw_validation_info(frame)
            
    #    # Store the hand landmarks data for external use
    #     self.hand_landmarks_data = results.multi_hand_landmarks
        
    #     # Add landmarks to the buffer with current timestamp - NEW ADDITION
    #     if results.multi_hand_landmarks:
    #         self.landmark_buffer.add_frame(results.multi_hand_landmarks)
        
    #     # Create a copy of the frame to draw on
    #     annotated_frame = frame.copy()
        
    #     # Draw FPS information
    #     cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30), 
    #                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
    #     # Draw hand landmarks if detected and if showing landmarks is enabled
    #     if self.show_landmarks and results.multi_hand_landmarks:
    #         for hand_landmarks in results.multi_hand_landmarks:
    #             self.mp_drawing.draw_landmarks(
    #                 annotated_frame,
    #                 hand_landmarks,
    #                 self.mp_hands.HAND_CONNECTIONS,
    #                 self.mp_drawing_styles.get_default_hand_landmarks_style(),
    #                 self.mp_drawing_styles.get_default_hand_connections_style()
    #             )
                
    #     return annotated_frame

    def _draw_selection_indicator(self, frame, hand_landmarks):
        """Draw visual feedback for selection gestures"""
        h, w, c = frame.shape
        
        # Get index fingertip position
        index_tip = hand_landmarks.landmark[8]
        x, y = int(index_tip.x * w), int(index_tip.y * h)
        
        if self.current_selection_gesture == "tap":
            # Draw tap indicator - blue circle
            cv2.circle(frame, (x, y), 20, (255, 0, 0), -1)
            cv2.circle(frame, (x, y), 25, (255, 255, 255), 2)
        elif self.current_selection_gesture == "pinch":
            # Draw pinch indicator - green circle
            cv2.circle(frame, (x, y), 20, (0, 255, 0), -1)
            cv2.circle(frame, (x, y), 25, (255, 255, 255), 2)

            
    def _process_frame(self, frame):
        """Process frame to detect hands and filter gestures"""
        # Your existing frame processing code...
            # Convert BGR to RGB for MediaPipe (MediaPipe requires RGB input)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with MediaPipe
        results = self.hands.process(rgb_frame)
        
        # Get the current time
        current_time = time.time()
        
        # Process gestures if hands are detected
        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) > 0:


            # Detect selection gestures (tap & pinch)
            self.current_selection_gesture = self.selection_detector.update(results.multi_hand_landmarks)
            
            # Draw different visual feedback for selection gestures
            if self.current_selection_gesture:
                self._draw_selection_indicator(frame, results.multi_hand_landmarks[0])
                
            # Add landmarks to the tracker
            self.landmark_tracker.add_landmarks(results.multi_hand_landmarks)
            
            # Get the primary hand landmarks
            primary_hand_landmarks = results.multi_hand_landmarks[0].landmark
            
            # Motion gesture processing with enhanced filtering
            if current_time - self.last_gesture_time > self.gesture_cooldown:
                # Detect and validate motion gestures
                motion, is_validated = self.landmark_tracker.detect_motion_gesture(
                    landmarks=primary_hand_landmarks,
                    threshold=self.motion_threshold,
                    confidence_threshold=self.confidence_threshold,
                    current_time=current_time
                )
                
                # Get current hand state for UI feedback
                hand_state = self.landmark_tracker.current_hand_state
                
                # Update gesture state based on filtering
                if motion not in ['stationary', 'insufficient_data', 'invalid_posture', 'transitioning', 'unclear_direction']:
                    # Store the detected motion for display
                    self.raw_motion = motion
                    
                    # Only update validated motion if it passes all filters
                    if is_validated:
                        self.validated_motion = motion
                        self.last_gesture_time = current_time
                        self.logger.info(f"Validated deliberate motion: {motion}")
        
        # Show validation and filtering debug info if enabled
        if self.show_validation_status and frame is not None:
            self._draw_validation_info(frame)
            
        
        # Show validation debug info if enabled
        if self.show_validation_status and frame is not None:
            self._draw_validation_info(frame)
            
       # Store the hand landmarks data for external use
        self.hand_landmarks_data = results.multi_hand_landmarks
        
        # Add landmarks to the buffer with current timestamp - NEW ADDITION
        if results.multi_hand_landmarks:
            self.landmark_buffer.add_frame(results.multi_hand_landmarks)
        
        # Create a copy of the frame to draw on
        annotated_frame = frame.copy()
        
        # Draw FPS information
        cv2.putText(annotated_frame, f"FPS: {self.fps:.1f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw hand landmarks if detected and if showing landmarks is enabled
        if self.show_landmarks and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
                
        return annotated_frame

    # New methods for motion analysis - NEW ADDITIONS

    def get_landmark_motion(self, hand_idx=0, landmark_idx=8, frames_back=5):
        """
        Calculate the motion vector of a specific landmark over the last n frames.
        
        Args:
            hand_idx: Hand index to track (default: 0 for first hand)
            landmark_idx: Landmark index to track (default: 8 for index fingertip)
            frames_back: Number of frames to analyze for motion (default: 5)
            
        Returns:
            Dictionary with motion data including direction and velocity
        """
        # Get the sequence of the specified landmark
        points, timestamps = self.landmark_buffer.get_landmark_sequence(
            hand_idx=hand_idx, landmark_idx=landmark_idx)
        
        if len(points) < 2:
            return {
                "direction": "unknown",
                "velocity": 0,
                "vector": (0, 0, 0)
            }
        
        # Use only the specified number of frames (or all if less)
        points = points[-min(frames_back, len(points)):]
        timestamps = timestamps[-min(frames_back, len(timestamps)):]
        
        # Calculate motion vector from oldest to newest position
        start_point = points[0]
        end_point = points[-1]
        time_diff = timestamps[-1] - timestamps[0]
        
        if time_diff <= 0:
            return {
                "direction": "unknown",
                "velocity": 0,
                "vector": (0, 0, 0)
            }
        
        # Calculate displacement vector
        dx = end_point[0] - start_point[0]
        dy = end_point[1] - start_point[1]
        dz = end_point[2] - start_point[2]
        
        # Velocity components
        vx = dx / time_diff
        vy = dy / time_diff
        vz = dz / time_diff
        
        # Velocity magnitude
        v_mag = np.sqrt(vx*vx + vy*vy + vz*vz)
        
        # Determine primary direction
        direction = "unknown"
        if abs(dx) > abs(dy) and abs(dx) > abs(dz):
            direction = "right" if dx > 0 else "left"
        elif abs(dy) > abs(dx) and abs(dy) > abs(dz):
            direction = "down" if dy > 0 else "up"
        elif abs(dz) > abs(dx) and abs(dz) > abs(dy):
            direction = "forward" if dz > 0 else "backward"
        
        return {
            "direction": direction,
            "velocity": v_mag,
            "vector": (vx, vy, vz)
        }
    
    def detect_swipe_gesture(self, hand_idx=0, threshold=0.1):
        """
        Detect swipe gestures based on index finger movement.
        
        Args:
            hand_idx: Hand index to track (default: 0 for first hand)
            threshold: Velocity threshold to consider a movement as a swipe
            
        Returns:
            Detected swipe direction or None
        """
        # Get motion of index fingertip
        motion = self.get_landmark_motion(hand_idx=hand_idx, landmark_idx=8)
        
        # Check if velocity is above threshold
        if motion["velocity"] > threshold:
            return f"swipe_{motion['direction']}"
        
        return None
    
    def get_whole_hand_motion(self, hand_idx=0, min_frames=5, displacement_threshold=0.03, 
                              consensus_threshold=0.8):
        """
        Analyze motion of all fingertips to determine if the entire hand is moving.
        Only detects directional movement when all five fingers show significant displacement.
        
        Args:
            hand_idx: Hand index (default: 0 for first hand)
            min_frames: Minimum number of frames needed for analysis (default: 5)
            displacement_threshold: Minimum displacement to consider as significant movement
            consensus_threshold: Proportion of fingers that must agree on direction (0.8 = 4/5)
            
        Returns:
            Dictionary with motion data including direction, velocity, and validation info
        """
        # Get trajectories for all fingertips
        fingertips = self.landmark_buffer.get_fingertips_sequence(hand_idx)
        
        # Check if we have enough data for all fingers
        if not all(finger in fingertips for finger in ['thumb', 'index', 'middle', 'ring', 'pinky']):
            return {
                "direction": "unknown",
                "velocity": 0,
                "valid": False,
                "reason": "missing_fingers"
            }
        
        # Check if we have enough frames for analysis
        finger_frames = [len(data['points']) for data in fingertips.values()]
        if min(finger_frames) < min_frames:
            return {
                "direction": "unknown",
                "velocity": 0,
                "valid": False,
                "reason": "insufficient_frames"
            }
        
        # Calculate displacement for each finger
        displacements = {}
        directions = {}
        velocities = {}
        
        for finger, data in fingertips.items():
            points = data['points']
            timestamps = data['timestamps']
            
            # Use the oldest and newest points
            start_point = points[0]
            end_point = points[-1]
            start_time = timestamps[0]
            end_time = timestamps[-1]
            
            # Time difference
            time_diff = end_time - start_time
            if time_diff <= 0:
                continue
            
            # Calculate 3D displacement vector
            dx = end_point[0] - start_point[0]
            dy = end_point[1] - start_point[1]
            dz = end_point[2] - start_point[2]
            
            # Overall displacement magnitude
            displacement = np.sqrt(dx*dx + dy*dy + dz*dz)
            displacements[finger] = displacement
            
            # Velocity
            velocity = displacement / time_diff
            velocities[finger] = velocity
            
            # Determine primary direction of this finger
            if displacement < displacement_threshold:
                # Movement too small to determine direction
                directions[finger] = "stationary"
            elif abs(dx) > abs(dy) and abs(dx) > abs(dz):
                # Horizontal motion
                directions[finger] = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) and abs(dy) > abs(dz):
                # Vertical motion
                directions[finger] = "down" if dy > 0 else "up"
            elif abs(dz) > abs(dx) and abs(dz) > abs(dy):
                # Z-axis motion
                directions[finger] = "forward" if dz > 0 else "backward"
            else:
                directions[finger] = "complex"
        
        # Check if all fingers have significant displacement
        significant_movement = all(d >= displacement_threshold for d in displacements.values())
        
        if not significant_movement:
            return {
                "direction": "stationary",
                "velocity": np.mean(list(velocities.values())),
                "valid": False,
                "reason": "insufficient_movement",
                "finger_displacements": displacements
            }
        
        # Check for directional consensus
        # Count occurrences of each direction
        direction_counts = {}
        for direction in directions.values():
            if direction != "stationary" and direction != "complex":
                direction_counts[direction] = direction_counts.get(direction, 0) + 1
        
        # Find most common direction
        if direction_counts:
            most_common_direction = max(direction_counts.items(), key=lambda x: x[1])
            direction_name = most_common_direction[0]
            direction_count = most_common_direction[1]
            
            # Check if enough fingers agree on the direction
            if direction_count >= len(directions) * consensus_threshold:
                # We have a valid hand direction
                return {
                    "direction": direction_name,
                    "velocity": np.mean(list(velocities.values())),
                    "valid": True,
                    "finger_directions": directions,
                    "finger_displacements": displacements,
                    "consensus": direction_count / len(directions)
                }
        
        # No clear consensus on direction
        return {
            "direction": "mixed",
            "velocity": np.mean(list(velocities.values())),
            "valid": False,
            "reason": "inconsistent_direction",
            "finger_directions": directions,
            "finger_displacements": displacements
        }
    
    def detect_whole_hand_gesture(self, hand_idx=0, displacement_threshold=0.03, 
                                 velocity_threshold=0.2):
        """
        Detect gestures based on whole hand movement, requiring all fingers
        to show consistent motion.
        
        Args:
            hand_idx: Hand index to track (default: 0 for first hand)
            displacement_threshold: Minimum displacement for significant movement
            velocity_threshold: Minimum velocity to trigger a gesture detection
            
        Returns:
            Detected gesture name or None
        """
        # Get whole hand motion analysis
        motion = self.get_whole_hand_motion(
            hand_idx=hand_idx, 
            displacement_threshold=displacement_threshold
        )
        
        # Only report valid whole-hand movements with sufficient velocity
        if motion["valid"] and motion["velocity"] > velocity_threshold:
            return f"hand_{motion['direction']}"
        
        return None
    
    def visualize_hand_motion(self, frame, hand_idx=0):
        """
        Visualize hand motion status on the frame.
        
        Args:
            frame: OpenCV frame to draw on
            hand_idx: Hand index to analyze
            
        Returns:
            Annotated frame
        """
        # Get whole hand motion
        motion = self.get_whole_hand_motion(hand_idx=hand_idx)
        
        # Draw the analysis results on the frame
        if motion["valid"]:
            # Valid motion detected
            color = (0, 255, 0)  # Green for valid motion
            status = f"Hand Direction: {motion['direction']} ({motion['velocity']:.2f})"
        else:
            # Invalid or insufficient motion
            color = (0, 0, 255)  # Red for invalid motion
            if "reason" in motion:
                status = f"Status: {motion['reason']}"
            else:
                status = "Status: Unknown issue"
        
        # Draw status text
        cv2.putText(frame, status, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Draw individual finger statuses if available
        if "finger_displacements" in motion:
            y_offset = 90
            for finger, displacement in motion["finger_displacements"].items():
                is_moving = displacement >= 0.03  # Use the same threshold
                finger_status = f"{finger}: {'Moving' if is_moving else 'Stable'} ({displacement:.4f})"
                finger_color = (0, 255, 0) if is_moving else (0, 165, 255)  # Green if moving, orange if stable
                cv2.putText(frame, finger_status, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, finger_color, 1)
                y_offset += 25
        
        return frame

    def get_landmark_trajectory(self, hand_idx=0, landmark_idx=8):
        """
        Get the complete trajectory of a specific landmark.
        
        Args:
            hand_idx: Hand index (default: 0 for first hand)
            landmark_idx: Landmark index (default: 8 for index fingertip)
            
        Returns:
            Array of landmark positions and timestamps
        """
        return self.landmark_buffer.get_landmark_sequence(hand_idx, landmark_idx)
    
    # def is_palm_open(self, hand_landmarks):
    #     """
    #     Determine if the palm is open (all fingers extended).
        
    #     Args:
    #         hand_landmarks: MediaPipe hand landmarks for a single hand
            
    #     Returns:
    #         Boolean indicating if palm is open
    #     """
    #     if not hand_landmarks:
    #         return False
            
    #     # MediaPipe landmark indices for fingertips and joints
    #     # Format: [tip, pip, mcp] for each finger
    #     finger_indices = {
    #         'thumb': [4, 3, 2],
    #         'index': [8, 6, 5],
    #         'middle': [12, 10, 9],
    #         'ring': [16, 14, 13],
    #         'pinky': [20, 18, 17]
    #     }
        
    #     # Check if each finger is extended
    #     fingers_extended = {}
        
    #     for finger, (tip_id, pip_id, mcp_id) in finger_indices.items():
    #         # Get landmarks
    #         tip = hand_landmarks.landmark[tip_id]
    #         pip = hand_landmarks.landmark[pip_id]
    #         mcp = hand_landmarks.landmark[mcp_id]
            
    #         # Special case for thumb due to its different orientation
    #         if finger == 'thumb':
    #             # For thumb, check if it's pointing away from palm
    #             # This is a simplified check - may need adjustment
    #             thumb_ip = hand_landmarks.landmark[3]  # IP joint
    #             thumb_cmc = hand_landmarks.landmark[1]  # CMC joint
                
    #             # Vector from CMC to IP
    #             vec1 = (thumb_ip.x - thumb_cmc.x, thumb_ip.y - thumb_cmc.y, thumb_ip.z - thumb_cmc.z)
    #             # Vector from IP to tip
    #             vec2 = (tip.x - thumb_ip.x, tip.y - thumb_ip.y, tip.z - thumb_ip.z)
                
    #             # Check if these vectors are roughly aligned (dot product > 0)
    #             dot_product = vec1[0]*vec2[0] + vec1[1]*vec2[1] + vec1[2]*vec2[2]
    #             fingers_extended['thumb'] = dot_product > 0
    #         else:
    #             # For other fingers, check if they are extended by comparing
    #             # the y coordinates (in image space, lower y is higher up)
    #             # and checking straightness
                
    #             # Calculate distance from MCP to fingertip directly
    #             direct_dist = np.sqrt(
    #                 (tip.x - mcp.x)**2 + 
    #                 (tip.y - mcp.y)**2 + 
    #                 (tip.z - mcp.z)**2
    #             )
                
    #             # Calculate distance along the finger joints
    #             joint_dist = np.sqrt(
    #                 (pip.x - mcp.x)**2 + 
    #                 (pip.y - mcp.y)**2 + 
    #                 (pip.z - mcp.z)**2
    #             ) + np.sqrt(
    #                 (tip.x - pip.x)**2 + 
    #                 (tip.y - pip.y)**2 + 
    #                 (tip.z - pip.z)**2
    #             )
                
    #             # If finger is extended, direct distance will be close to joint distance
    #             # If bent, direct distance will be much less
    #             straightness = direct_dist / joint_dist if joint_dist > 0 else 0
                
    #             # Consider finger extended if reasonably straight and pointing outward
    #             fingers_extended[finger] = (straightness > 0.7 and tip.y < mcp.y)
        
    #     # Palm is considered open if all fingers are extended
    #     # Or if at least 4 out of 5 fingers (excluding thumb) are extended
    #     num_extended = sum(1 for extended in fingers_extended.values() if extended)
    #     return num_extended >= 4  # Allow one finger to be bent
    
    # def is_palm_open(self, hand_idx=0, extension_threshold=0.5):
    #     """
    #     Determine if the palm is open by checking finger extension.
        
    #     Args:
    #         hand_idx: Hand index (default: 0 for first hand)
    #         extension_threshold: Threshold to consider a finger extended
            
    #     Returns:
    #         Boolean indicating if palm is open, and confidence score
    #     """
    #     # Check if we have hand landmarks data
    #     if not self.hand_landmarks_data or hand_idx >= len(self.hand_landmarks_data):
    #         return False, 0.0
            
    #     # Get the landmarks for the specified hand
    #     hand_landmarks = self.hand_landmarks_data[hand_idx]
        
    #     # Check finger extension
    #     extended_fingers = 0
        
    #     # MediaPipe hand landmark indices
    #     # Wrist: 0
    #     # Fingertips: 4 (thumb), 8 (index), 12 (middle), 16 (ring), 20 (pinky)
    #     # Knuckles: 5 (index), 9 (middle), 13 (ring), 17 (pinky)
        
    #     # Get coordinates of important landmarks
    #     wrist = hand_landmarks.landmark[0]
    #     palm_center = hand_landmarks.landmark[9]  # Middle finger knuckle as palm center
        
    #     # Check each finger (excluding thumb which has different mechanics)
    #     for finger_idx, tip_idx in enumerate([8, 12, 16, 20]):  # Index, middle, ring, pinky tips
    #         knuckle_idx = 5 + (finger_idx * 4)  # 5, 9, 13, 17
            
    #         fingertip = hand_landmarks.landmark[tip_idx]
    #         knuckle = hand_landmarks.landmark[knuckle_idx]
            
    #         # Calculate vectors
    #         # Vector from knuckle to palm center
    #         v_knuckle_to_palm = np.array([
    #             palm_center.x - knuckle.x,
    #             palm_center.y - knuckle.y,
    #             palm_center.z - knuckle.z
    #         ])
            
    #         # Vector from knuckle to fingertip
    #         v_knuckle_to_tip = np.array([
    #             fingertip.x - knuckle.x,
    #             fingertip.y - knuckle.y,
    #             fingertip.z - knuckle.z
    #         ])
            
    #         # Normalize vectors
    #         knuckle_to_palm_length = np.sqrt(np.sum(v_knuckle_to_palm**2))
    #         knuckle_to_tip_length = np.sqrt(np.sum(v_knuckle_to_tip**2))
            
    #         if knuckle_to_palm_length > 0 and knuckle_to_tip_length > 0:
    #             v_knuckle_to_palm = v_knuckle_to_palm / knuckle_to_palm_length
    #             v_knuckle_to_tip = v_knuckle_to_tip / knuckle_to_tip_length
                
    #             # Calculate dot product to determine finger extension
    #             # If dot product is negative, finger is pointing away from palm
    #             dot_product = np.dot(v_knuckle_to_palm, v_knuckle_to_tip)
                
    #             if dot_product < -extension_threshold:  # Negative means pointing away from palm
    #                 extended_fingers += 1
        
    #     # Special case for thumb
    #     thumb_tip = hand_landmarks.landmark[4]
    #     thumb_base = hand_landmarks.landmark[2]
    #     index_base = hand_landmarks.landmark[5]
        
    #     # Calculate vector from thumb base to index base (across palm)
    #     v_across_palm = np.array([
    #         index_base.x - thumb_base.x,
    #         index_base.y - thumb_base.y,
    #         index_base.z - thumb_base.z
    #     ])
        
    #     # Vector from thumb base to thumb tip
    #     v_thumb_base_to_tip = np.array([
    #         thumb_tip.x - thumb_base.x,
    #         thumb_tip.y - thumb_base.y,
    #         thumb_tip.z - thumb_base.z
    #     ])
        
    #     # Normalize vectors
    #     across_palm_length = np.sqrt(np.sum(v_across_palm**2))
    #     thumb_length = np.sqrt(np.sum(v_thumb_base_to_tip**2))
        
    #     if across_palm_length > 0 and thumb_length > 0:
    #         v_across_palm = v_across_palm / across_palm_length
    #         v_thumb_base_to_tip = v_thumb_base_to_tip / thumb_length
            
    #         # Calculate dot product
    #         thumb_dot = np.dot(v_across_palm, v_thumb_base_to_tip)
            
    #         # Thumb is extended if it's pointing perpendicular to or away from the palm
    #         if thumb_dot < extension_threshold:
    #             extended_fingers += 1
        
    #     # Calculate confidence score (0 to 1)
    #     confidence = extended_fingers / 5.0
        
    #     # Consider palm open if majority of fingers are extended
    #     is_open = extended_fingers >= 3
        
    #     return is_open, confidence

    def is_palm_open(self, hand_idx=0, extension_threshold=0.04):
        """
        Determine if the palm is open by checking finger extension based on fingertip-to-knuckle distances.

        Args:
            hand_idx: Index of the hand (default is 0 for first hand)
            extension_threshold: Minimum distance to consider a finger extended

        Returns:
            Tuple (is_open: bool, confidence: float)
        """

        if not self.hand_landmarks_data or hand_idx >= len(self.hand_landmarks_data):
            return False, 0.0

        hand_landmarks = self.hand_landmarks_data[hand_idx]
        extended_fingers = 0

        # Helper function for distance check
        def is_finger_extended(tip_idx, knuckle_idx, threshold):
            tip = hand_landmarks.landmark[tip_idx]
            knuckle = hand_landmarks.landmark[knuckle_idx]
            distance = np.linalg.norm([
                tip.x - knuckle.x,
                tip.y - knuckle.y,
                tip.z - knuckle.z
            ])
            return distance > threshold

        # Check index, middle, ring, and pinky fingers
        for finger_idx, tip_idx in enumerate([8, 12, 16, 20]):  # Fingertips
            knuckle_idx = 5 + finger_idx * 4  # Knuckles: 5, 9, 13, 17
            if is_finger_extended(tip_idx, knuckle_idx, extension_threshold):
                extended_fingers += 1

        # Check thumb separately (tip: 4, base: 2), compare to index base (5)
        thumb_tip = hand_landmarks.landmark[4]
        thumb_base = hand_landmarks.landmark[2]
        index_base = hand_landmarks.landmark[5]
        thumb_distance = np.linalg.norm([
            thumb_tip.x - index_base.x,
            thumb_tip.y - index_base.y,
            thumb_tip.z - index_base.z
        ])
        if thumb_distance > extension_threshold:
            extended_fingers += 1

        confidence = extended_fingers / 5.0
        is_open = extended_fingers >= 3  # Majority of fingers extended

        return is_open, confidence

    def get_palm_state(self):
        """
        Get the current state of the palm for the most recent frame.
        
        Returns:
            Dict with palm state information
        """
        if not self.hand_landmarks_data or not self.hand_landmarks_data[0]:
            return {"palm_open": False, "reason": "No hand detected"}
            
        # Check palm state for the first detected hand
        palm_open = self.is_palm_open(self.hand_landmarks_data[0])
        
        if palm_open:
            return {"palm_open": True, "reason": "Palm is open"}
        else:
            return {"palm_open": False, "reason": "Palm is closed or fingers are bent"}
    
    def detect_whole_hand_gesture(self, hand_idx=0, displacement_threshold=0.03, 
                                 velocity_threshold=0.2):
        """
        Detect gestures based on whole hand movement, requiring:
        1. All fingers to show consistent motion
        2. Palm to be in open state
        
        Args:
            hand_idx: Hand index to track (default: 0 for first hand)
            displacement_threshold: Minimum displacement for significant movement
            velocity_threshold: Minimum velocity to trigger a gesture detection
            
        Returns:
            Detected gesture name or None
        """
        # First, check if palm is open - no gesture detection if palm is closed
        if not self.hand_landmarks_data:
            return None
            
        palm_state = self.get_palm_state()
        if not palm_state["palm_open"]:
            # Palm is not open, no gesture detection
            return None
        
        # If palm is open, proceed with whole hand motion analysis
        motion = self.get_whole_hand_motion(
            hand_idx=hand_idx, 
            displacement_threshold=displacement_threshold
        )
        
        # Only report valid whole-hand movements with sufficient velocity
        if motion["valid"] and motion["velocity"] > velocity_threshold:
            return f"hand_{motion['direction']}"
        
        return None
    
    def visualize_hand_motion(self, frame, hand_idx=0):
        """
        Visualize hand motion status on the frame, now including palm state.
        
        Args:
            frame: OpenCV frame to draw on
            hand_idx: Hand index to analyze
            
        Returns:
            Annotated frame
        """
        # First check palm state
        palm_state = self.get_palm_state()
        
        # Draw palm state
        if palm_state["palm_open"]:
            cv2.putText(frame, "Palm: OPEN - Gesture detection active", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, f"Palm: CLOSED - Gesture detection disabled ({palm_state['reason']})", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # If palm is closed, don't proceed with motion analysis
            return frame
        
        # Get whole hand motion (only proceed if palm is open)
        motion = self.get_whole_hand_motion(hand_idx=hand_idx)
        
        # Draw the analysis results
        if motion["valid"]:
            # Valid motion detected
            color = (0, 255, 0)  # Green for valid motion
            status = f"Hand Direction: {motion['direction']} ({motion['velocity']:.2f})"
        else:
            # Invalid or insufficient motion
            color = (0, 0, 255)  # Red for invalid motion
            if "reason" in motion:
                status = f"Status: {motion['reason']}"
            else:
                status = "Status: Unknown issue"
        
        # Draw status text
        cv2.putText(frame, status, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Draw individual finger statuses if available
        if "finger_displacements" in motion:
            y_offset = 120
            for finger, displacement in motion["finger_displacements"].items():
                is_moving = displacement >= 0.03  # Use the same threshold
                finger_status = f"{finger}: {'Moving' if is_moving else 'Stable'} ({displacement:.4f})"
                finger_color = (0, 255, 0) if is_moving else (0, 165, 255)  # Green if moving, orange if stable
                cv2.putText(frame, finger_status, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, finger_color, 1)
                y_offset += 25
        
        return frame

    def compute_movement_vector(self, hand_idx=0, frames=10):
        """
        Compute the movement vector and velocity from the stored landmark buffer.
        Uses palm center (landmark 9) as reference point for hand position.
        
        Args:
            hand_idx: Hand index to track
            frames: Number of frames to analyze (up to buffer size)
            
        Returns:
            Dictionary with movement data
        """
        # Palm center is approximated by landmark 9 (middle finger MCP joint)
        palm_trajectory, timestamps = self.landmark_buffer.get_landmark_sequence(
            hand_idx=hand_idx, landmark_idx=9)
        
        if len(palm_trajectory) < 2:
            return {
                "vector": np.zeros(3),
                "velocity": 0.0,
                "direction": "none",
                "displacement": 0.0,
                "duration": 0.0,
                "valid": False
            }
        
        # Limit to specified number of frames
        actual_frames = min(frames, len(palm_trajectory))
        palm_trajectory = palm_trajectory[-actual_frames:]
        timestamps = timestamps[-actual_frames:]
        
        # Calculate movement vector from oldest to newest position
        start_position = palm_trajectory[0]
        end_position = palm_trajectory[-1]
        
        # Calculate time duration
        start_time = timestamps[0]
        end_time = timestamps[-1]
        duration = end_time - start_time
        
        if duration <= 0.001:  # Avoid division by zero
            return {
                "vector": np.zeros(3),
                "velocity": 0.0,
                "direction": "none",
                "displacement": 0.0,
                "duration": 0.0,
                "valid": False
            }
        
        # Calculate displacement vector
        displacement_vector = end_position - start_position
        
        # Calculate total displacement (Euclidean distance)
        displacement = np.linalg.norm(displacement_vector)
        
        # Calculate velocity (displacement/time)
        velocity = displacement / duration
        
        # Determine primary direction
        abs_dx = abs(displacement_vector[0])
        abs_dy = abs(displacement_vector[1])
        abs_dz = abs(displacement_vector[2])
        
        direction = "none"
        if abs_dx > abs_dy and abs_dx > abs_dz:
            direction = "right" if displacement_vector[0] > 0 else "left"
        elif abs_dy > abs_dx and abs_dy > abs_dz:
            direction = "down" if displacement_vector[1] > 0 else "up"
        elif abs_dz > abs_dx and abs_dz > abs_dy:
            direction = "forward" if displacement_vector[2] > 0 else "backward"
        
        return {
            "vector": displacement_vector,
            "velocity": velocity,
            "direction": direction,
            "displacement": displacement,
            "duration": duration,
            "valid": True,
            "directional_components": {
                "dx": displacement_vector[0],
                "dy": displacement_vector[1],
                "dz": displacement_vector[2]
            }
        }
    
    def detect_swipe_gesture(self, min_velocity=0.3, min_displacement=0.08, hand_idx=0):

        """
        Detect swipe gestures based on palm movement.
        
        Args:
            min_velocity: Minimum velocity to consider as a swipe
            min_displacement: Minimum displacement to consider as a swipe
            hand_idx: Hand index to track
            
        Returns:
            Detected swipe direction or None
        """
        # First check if palm is open
        is_palm_open, confidence = self.is_palm_open(hand_idx=hand_idx)
        
        if not is_palm_open or confidence < 0.7:
            return None
        
        # Compute movement
        movement = self.compute_movement_vector(hand_idx=hand_idx)
        
        if not movement["valid"]:
            return None
        
        # Check if movement exceeds thresholds
        if movement["velocity"] < min_velocity or movement["displacement"] < min_displacement:
            return None
        
        # Map direction to swipe
        if movement["direction"] in ["left", "right", "up", "down"]:
            return f"swipe_{movement['direction']}"
        
        return None
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

    def get_current_gestures(self):
        """Get current gesture status for API or UI"""
        return {
            'raw_gesture': self.raw_gesture,
            'validated_gesture': self.validated_gesture,
            'raw_motion': self.raw_motion,
            'validated_motion': self.validated_motion,
            'debug': self.landmark_tracker.get_debug_info() if self.show_validation_status else None
        }
    
    def toggle_validation_display(self):
        """Toggle visibility of validation debug info"""
        self.show_validation_status = not self.show_validation_status
        return self.show_validation_status
    
    # def _draw_validation_info(self, frame):
    #     """Draw validation information on frame for debugging"""
    #     # Get debug info from tracker
    #     debug_info = self.landmark_tracker.get_debug_info()
        
    #     # Set text properties
    #     font = cv2.FONT_HERSHEY_SIMPLEX
    #     font_scale = 0.6
    #     thickness = 1
    #     padding = 10
    #     line_height = 25
        
    #     # Background rectangle
    #     overlay = frame.copy()
    #     cv2.rectangle(overlay, (10, 10), (350, 170), (0, 0, 0), -1)
    #     cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
    #     # Draw text lines
    #     lines = [
    #         f"Raw motion: {self.raw_motion or 'None'}",
    #         f"Validated: {self.validated_motion or 'None'}",
    #         f"Duration: {debug_info['tracking_duration']:.2f}s / {self.landmark_tracker.min_gesture_duration:.2f}s",
    #         f"Posture: {'Valid' if debug_info['posture_valid'] else 'Invalid'}",
    #         f"Reason: {debug_info['validation_reason']}"
    #     ]
        
    #     y = 30
    #     for line in lines:
    #         cv2.putText(frame, line, (padding, y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
    #         y += line_height

    def _draw_validation_info(self, frame):
        """Draw enhanced validation information on frame for debugging"""
        # Get debug info from tracker
        debug_info = self.landmark_tracker.get_debug_info()
        
        # Set text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        padding = 10
        line_height = 25
        
        # Background rectangle
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 230), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Color coding based on hand state
        color_map = {
            "UNKNOWN": (128, 128, 128),  # Gray
            "IDLE": (255, 0, 0),         # Blue
            "TRANSITIONING": (0, 165, 255), # Orange
            "DELIBERATE": (0, 255, 0)    # Green
        }
        state_color = color_map.get(debug_info["hand_state"], (255, 255, 255))
        
        # Draw text lines
        lines = [
            f"Hand state: {debug_info['hand_state']}",
            f"Raw motion: {self.raw_motion or 'None'}",
            f"Validated: {self.validated_motion or 'None'}",
            f"Posture: {'Valid' if debug_info['posture_valid'] else 'Invalid'}",
            f"Velocity: {debug_info['avg_velocity']:.3f}",
            f"Motion consistency: {debug_info['motion_consistency']:.2f}",
            f"Direction consistency: {debug_info.get('direction_consistency', 0):.2f}",
            f"Duration: {debug_info['tracking_duration']:.2f}s / {self.landmark_tracker.min_gesture_duration:.2f}s",
            f"Reason: {debug_info['validation_reason']}"
        ]
        
        y = 35
        # First draw hand state with special highlighting
        cv2.putText(frame, f"Hand state: {debug_info['hand_state']}", 
                    (padding, y), font, font_scale, state_color, thickness, cv2.LINE_AA)
        y += line_height
        
        # Then draw the rest of the lines
        for line in lines[1:]:
            cv2.putText(frame, line, (padding, y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
            y += line_height
    def get_processed_frame(self):
        """
        Get the latest processed frame in a thread-safe manner.
        
        Returns:
            np.ndarray: A copy of the most recent processed frame, or None if no frame is available
        """
        with self.lock:
            if self.processed_frame is None:
                return None
            # Return a copy to prevent modification of the internal frame
            return self.processed_frame.copy()