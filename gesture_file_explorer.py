# gesture_file_explorer.py

import cv2
import time
import threading
from camera import Camera
from gesture_recognizer import GestureRecognizer
from file_system_manager import FileSystemManager
from file_system_gesture_interface import FileSystemGestureInterface

def display_file_explorer_ui(frame, state_info):
    """Display file explorer UI overlay on the camera frame."""
    # Get information from state
    current_dir = state_info['current_directory']
    items = state_info['items']
    selected_idx = state_info['selected_index']
    message = state_info.get('message', '')
    
    # Set up constants for UI display
    font = cv2.FONT_HERSHEY_SIMPLEX
    bg_color = (50, 50, 50)  # Dark gray background
    text_color = (255, 255, 255)  # White text
    select_color = (50, 200, 50)  # Green for selection
    
    # Draw top info bar with current directory
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), bg_color, -1)
    cv2.putText(frame, f"Directory: {current_dir}", (10, 30), font, 0.6, text_color, 1)
    
    # Draw bottom message bar
    cv2.rectangle(frame, (0, frame.shape[0] - 40), (frame.shape[1], frame.shape[0]), bg_color, -1)
    cv2.putText(frame, message, (10, frame.shape[0] - 15), font, 0.6, text_color, 1)
    
    # Draw file list panel on the right
    panel_width = 250
    panel_x = frame.shape[1] - panel_width
    cv2.rectangle(frame, (panel_x, 40), (frame.shape[1], frame.shape[0] - 40), bg_color, -1)
    
    # Draw directory items
    item_height = 30
    visible_items = min(12, len(items))  # Show at most 12 items at once
    
    # Determine start index to keep selection in view
    start_idx = max(0, min(selected_idx, len(items) - visible_items))
    
    for i in range(start_idx, start_idx + visible_items):
        if i >= len(items):
            break
            
        item = items[i]
        y_pos = 70 + (i - start_idx) * item_height
        
        # Highlight selected item
        if i == selected_idx:
            cv2.rectangle(frame, (panel_x, y_pos - 20), (frame.shape[1], y_pos + 10), select_color, -1)
        
        # Add folder icon indicator
        icon = "📁 " if item['is_dir'] else "📄 "
        cv2.putText(frame, icon + item['name'], (panel_x + 10, y_pos), font, 0.5, text_color, 1)
    
    # Draw gesture instructions
    y_pos = frame.shape[0] - 180
    cv2.putText(frame, "Gesture Controls:", (10, y_pos), font, 0.6, text_color, 1)
    cv2.putText(frame, "👆 Point Up: Select Previous", (20, y_pos + 30), font, 0.5, text_color, 1)
    cv2.putText(frame, "👇 Point Down: Select Next", (20, y_pos + 60), font, 0.5, text_color, 1)
    cv2.putText(frame, "👈 Point Left: Go Up Directory", (20, y_pos + 90), font, 0.5, text_color, 1)
    cv2.putText(frame, "👉 Point Right: Enter Directory", (20, y_pos + 120), font, 0.5, text_color, 1)
    cv2.putText(frame, "✋ Open Palm: Refresh", (20, y_pos + 150), font, 0.5, text_color, 1)
    
    return frame

def main():
    
    # Initialize the camera and gesture recognizer
    camera = Camera(mirror=True)
    gesture_recognizer = GestureRecognizer(buffer_size=5)
    
    # Initialize file system manager
    file_manager = FileSystemManager()
    
    # Create gesture-file system interface
    gesture_interface = FileSystemGestureInterface(file_manager, gesture_recognizer)
    
    print(f"Starting file system gesture control in: {file_manager.get_current_path()}")
    
    # Initialize operation state
    state_info = gesture_interface._get_current_state()
    state_info['message'] = "Welcome to GestureDrive File Explorer"
    
    try:
        camera.start()
        last_gesture_time = 0
        gesture_cooldown = 0.5  # seconds
        
        while True:
            # Get the latest processed frame
            frame = camera.get_processed_frame()
            if frame is None:
                continue
                
            # Get the latest gesture if hand landmarks are available
            if camera.hand_landmarks_data:
                # Process first detected hand's landmarks
                current_gesture = gesture_recognizer.update_gesture(camera.hand_landmarks_data[0])
                
                # Process gesture with cooldown
                current_time = time.time()
                if current_time - last_gesture_time >= gesture_cooldown:
                    # Check for meaningful gestures
                    if current_gesture in ["point_up", "point_down", "point_left", "point_right", "open_palm"]:
                        state_info = gesture_interface.process_gesture(current_gesture)
                        last_gesture_time = current_time
            
            # Add file explorer UI to the frame
            display_frame = display_file_explorer_ui(frame.copy(), state_info)
            
            # Show the resulting frame
            cv2.imshow('GestureDrive File Explorer', display_frame)
            
            # Break loop on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # Clean up resources
        camera.stop()
        gesture_interface.cleanup()
        cv2.destroyAllWindows()
        
if __name__ == "__main__":
    main()