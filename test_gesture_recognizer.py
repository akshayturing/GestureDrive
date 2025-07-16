# import cv2
# import time
# from camera import Camera
# from gesture_recognizer import GestureRecognizer

# def main():
#     # Initialize camera
#     camera = Camera(camera_id=0, width=640, height=480)
#     try:
#         camera.start()
        
#         # Initialize gesture recognizer
#         recognizer = GestureRecognizer(buffer_size=5)
        
#         print("Camera started. Press 'q' to quit.")
        
#         while True:
#             # Get processed frame
#             frame = camera.get_frame(processed=True)
#             if frame is None:
#                 time.sleep(0.1)
#                 continue
            
#             # Get hand landmarks and recognize gesture
#             hand_landmarks = camera.get_hand_landmarks()
#             if hand_landmarks:
#                 # Use the first hand's landmarks
#                 gesture = recognizer.update_gesture(hand_landmarks[0])
#                 command = recognizer.get_command(gesture)
                
#                 # Display gesture and command
#                 cv2.putText(frame, f"Gesture: {gesture}", (10, 60), 
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
#                 cv2.putText(frame, f"Command: {command}", (10, 90), 
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
#             # Show frame
#             cv2.imshow('GestureDrive Test', frame)
            
#             # Check for quit command
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
                
#     finally:
#         # Clean up
#         camera.stop()
#         cv2.destroyAllWindows()
#         print("Camera stopped and resources released.")

# if __name__ == "__main__":
#     main()

# Enhancement for test_gesture_recognition.py

# Import modules
import cv2
import time
from camera import Camera
from gesture_recognizer import GestureRecognizer

def main():
    # Initialize camera
    camera = Camera(camera_id=0, width=640, height=480)
    camera.start()
    
    # Initialize gesture recognizer
    recognizer = GestureRecognizer()
    
    # Wait for camera to initialize
    time.sleep(2)
    
    try:
        while True:
            # Get the latest processed frame
            with camera.lock:
                if camera.processed_frame is None:
                    continue
                frame = camera.processed_frame.copy()
            
            # Get current hand landmarks
            if camera.hand_landmarks_data:
                # Static gesture recognition
                for hand_landmarks in camera.hand_landmarks_data:
                    gesture = recognizer.update_gesture(hand_landmarks)
                    command = recognizer.get_command(gesture)
                    
                    # Display static gesture and command
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, f"Command: {command}", (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Dynamic gesture detection using motion tracking
                motion = camera.get_landmark_motion(landmark_idx=8)
                swipe = camera.detect_swipe_gesture(threshold=0.15)
                
                # Display motion information
                cv2.putText(frame, f"Motion: {motion['direction']} ({motion['velocity']:.2f})", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                if swipe:
                    cv2.putText(frame, f"Swipe detected: {swipe}", 
                               (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('GestureDrive', frame)
            
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up
        camera.is_running = False
        if camera.thread:
            camera.thread.join(timeout=1.0)
        if hasattr(camera, 'cap') and camera.cap:
            camera.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()