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