import cv2
import threading
import time
import numpy as np
import mediapipe as mp

class Camera:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.video_capture = None
        self.is_running = False
        self.lock = threading.Lock()
        self.frame = None
        self.fps = 0
        self.last_frame_time = time.time()
        self.frame_count = 0
        
        # MediaPipe hand detection (will be used later)
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = None
        
        # Settings
        self.mirror = True
        self.show_landmarks = True
        self.min_detection_confidence = 0.7
        self.min_tracking_confidence = 0.5

    def start(self):
        """Initialize and start the camera capture thread"""
        if self.is_running:
            print("Camera is already running")
            return
        
        self.video_capture = cv2.VideoCapture(self.camera_id)
        if not self.video_capture.isOpened():
            raise ValueError(f"Unable to open camera {self.camera_id}")
            
        # Set camera properties
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Start capture thread
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()
        
        # Initialize MediaPipe hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        
        print(f"Camera {self.camera_id} started")

    def stop(self):
        """Stop the camera capture"""
        self.is_running = False
        if self.thread:
            self.thread.join()
        if self.video_capture:
            self.video_capture.release()
        if self.hands:
            self.hands.close()
        print(f"Camera {self.camera_id} stopped")

    def _capture_loop(self):
        """Camera capture loop that runs in a separate thread"""
        while self.is_running:
            ret, frame = self.video_capture.read()
            if not ret:
                print("Failed to capture frame")
                time.sleep(0.1)
                continue
                
            # Calculate FPS
            current_time = time.time()
            self.frame_count += 1
            if (current_time - self.last_frame_time) >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_frame_time = current_time
            
            # Mirror the frame if needed
            if self.mirror:
                frame = cv2.flip(frame, 1)
            
            # Process the frame for hand detection (basic implementation)
            self._process_frame(frame)
            
            # Update the current frame (thread-safe)
            with self.lock:
                self.frame = frame

    def _process_frame(self, frame):
        """Process the frame for hand detection and visualization"""
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        if self.hands:
            results = self.hands.process(rgb_frame)
            
            # Draw hand landmarks if detected and enabled
            if results.multi_hand_landmarks and self.show_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )
                    
            # Add FPS counter to the frame
            cv2.putText(
                frame, 
                f"FPS: {self.fps}", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (0, 255, 0), 
                2
            )

    def get_frame(self):
        """Get the current frame as JPEG bytes"""
        if not self.is_running:
            return None
        
        with self.lock:
            if self.frame is None:
                return None
            # Encode the frame as JPEG
            ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            
        return jpeg.tobytes() if ret else None

# Create a camera instance for the application
camera = None

def init_camera(camera_id=0):
    """Initialize the camera with the given ID"""
    global camera
    camera = Camera(camera_id)
    camera.start()
    return camera

def get_camera():
    """Get the current camera instance"""
    global camera
    if camera is None:
        camera = init_camera()
    return camera