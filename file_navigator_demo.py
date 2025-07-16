import cv2
import time
import numpy as np

from camera import Camera
from gesture_navigation import NavigationGestureController

def draw_file_browser(frame, nav_controller):
    """Draw file browser interface on the frame"""
    view = nav_controller.get_current_view()
    
    # Draw current directory
    cv2.putText(frame, f"Directory: {view['current_directory']}", 
               (frame.shape[1] - 400, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Draw file/folder list
    y_offset = 70
    for i, item in enumerate(view['directory_contents']):
        # Highlight the selected item
        if i == view['scroll_position']:
            color = (0, 255, 255)  # Yellow for selected item
            cv2.rectangle(frame, (frame.shape[1] - 410, y_offset - 20), 
                         (frame.shape[1] - 10, y_offset + 5), color, 2)
        else:
            color = (200, 200, 200)  # Light gray for other items
            
        # Indicate if item is a folder or file
        is_folder = not item.endswith('.txt')
        icon = "[📁]" if is_folder else "[📄]"
        
        cv2.putText(frame, f"{icon} {item}", 
                   (frame.shape[1] - 400, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        y_offset += 40
    
    # Draw gesture hints
    hints_y = frame.shape[0] - 140
    cv2.putText(frame, "Gesture Controls:", (20, hints_y), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, "👈 Swipe Left: Go back", (30, hints_y + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, "👉 Swipe Right: Enter folder", (30, hints_y + 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, "👆 Swipe Up: Scroll up", (30, hints_y + 90), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, "👇 Swipe Down: Scroll down", (30, hints_y + 120), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    return frame


def main():
    # Initialize camera
    camera = Camera(camera_id=0, width=640, height=480)
    camera.start()
    
    # Initialize navigation controller
    nav_controller = NavigationGestureController(
        min_velocity=0.3,       # Adjust based on testing
        min_displacement=0.08,  # Adjust based on testing
        cooldown_time=1.0       # Prevent rapid-fire gestures
    )
    
    # Wait for camera to initialize
    time.sleep(2)
    
    # Variables for gesture animation
    action_message = ""
    message_time = 0
    message_duration = 2.0  # Show message for 2 seconds
    
    try:
        while True:
            # Get the latest processed frame
            with camera.lock:
                if camera.processed_frame is None:
                    continue
                frame = camera.processed_frame.copy()
            is_palm_open, confidence = False, 0.0
            # Track hand landmarks and status
            if camera.hand_landmarks_data:
                # Check palm state
                
                
                is_palm_open, confidence = camera.is_palm_open(hand_idx=0)
    
                palm_status = f"Palm: {'Open' if is_palm_open else 'Closed'} ({confidence:.2f})"
                palm_color = (0, 255, 0) if is_palm_open else (0, 0, 255)
                
                cv2.putText(frame, palm_status, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, palm_color, 2)
                
                # Display movement data when palm is open
                if is_palm_open:
                    # Compute palm movement
                    movement = camera.compute_movement_vector()
                    
                    # Display velocity and direction
                    if movement["valid"]:
                        move_info = f"Movement: {movement['direction']} " \
                                    f"({movement['velocity']:.2f}, {movement['displacement']:.2f})"
                        cv2.putText(frame, move_info, (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
                    
                    # Detect navigation gesture
                    nav_action = nav_controller.detect_navigation_gesture(camera)
                    
                    # Execute the action if detected
                    if nav_action:
                        result = nav_controller.execute_navigation_action(nav_action)
                        action_message = result
                        message_time = time.time()
                
            # Display action message with fade-out effect
            current_time = time.time()
            if current_time - message_time < message_duration:
                # Calculate fade alpha (1.0 at start, 0.0 at end)
                alpha = 1.0 - ((current_time - message_time) / message_duration)
                
                # Display with alpha-based color intensity
                color_intensity = int(255 * alpha)
                cv2.putText(frame, action_message, 
                           (frame.shape[1]//2 - 150, frame.shape[0]//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, 
                           (0, color_intensity, color_intensity), 2)
            
            # Draw file browser UI
            frame = draw_file_browser(frame, nav_controller)
            
            # Display the frame
            cv2.imshow('GestureDrive - File Navigator', frame)
            
            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up resources
        camera.is_running = False
        if camera.thread:
            camera.thread.join(timeout=1.0)
        if hasattr(camera, 'cap') and camera.cap:
            camera.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
