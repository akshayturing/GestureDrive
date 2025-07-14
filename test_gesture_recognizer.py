import cv2
import time
from camera import Camera
from gesture_recognizer import GestureRecognizer

def main():
    # Initialize camera
    camera = Camera(camera_id=0, width=640, height=480)
    try:
        camera.start()
        
        # Initialize gesture recognizer
        recognizer = GestureRecognizer(buffer_size=5)
        
        print("Camera started. Press 'q' to quit.")
        
        while True:
            # Get processed frame
            frame = camera.get_frame(processed=True)
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Get hand landmarks and recognize gesture
            hand_landmarks = camera.get_hand_landmarks()
            if hand_landmarks:
                # Use the first hand's landmarks
                gesture = recognizer.update_gesture(hand_landmarks[0])
                command = recognizer.get_command(gesture)
                
                # Display gesture and command
                cv2.putText(frame, f"Gesture: {gesture}", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(frame, f"Command: {command}", (10, 90), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow('GestureDrive Test', frame)
            
            # Check for quit command
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # Clean up
        camera.stop()
        cv2.destroyAllWindows()
        print("Camera stopped and resources released.")

if __name__ == "__main__":
    main()