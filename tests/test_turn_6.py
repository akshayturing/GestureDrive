# Import the necessary modules
from core.camera import Camera
import cv2
import time

# Create and initialize the camera
camera = Camera(camera_id=0, width=640, height=480)
camera.start()

try:
    print("Press 'q' to quit")
    
    while True:
        # Get processed frame
        frame = camera.get_frame(processed=True)
        if frame is None:
            time.sleep(0.1)
            continue
        
        # Display the frame
        cv2.imshow('GestureDrive - Hand Landmark Tracking', frame)
        
        # Check for quit command
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
finally:
    # Clean up
    camera.stop()
    cv2.destroyAllWindows()
    print("Camera stopped and resources released.")