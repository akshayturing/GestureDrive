import math

class GestureRecognizer:
    def __init__(self, buffer_size=5):
        # Define recognized gestures and their corresponding commands
        self.gestures = {
            "point_up": "Move Forward",
            "point_down": "Move Backwards",
            "point_left": "Turn Left",
            "point_right": "Turn Right",
            "open_palm": "Stop",
            "unknown": "No Action"
        }
        
        # Buffer for smoothing gesture recognition
        self.buffer_size = buffer_size
        self.gesture_buffer = []
        self.current_gesture = "unknown"
    
    def recognize_gesture(self, hand_landmarks):
        """Recognize gesture based on hand landmarks"""
        if not hand_landmarks:
            return "unknown"
        
        landmarks = hand_landmarks.landmark
        
        # Check finger extension
        thumb_extended = self._is_thumb_extended(landmarks)
        index_extended = self._is_finger_extended(landmarks, 8, 6, 5)  # tip, pip, mcp
        middle_extended = self._is_finger_extended(landmarks, 12, 10, 9)
        ring_extended = self._is_finger_extended(landmarks, 16, 14, 13)
        pinky_extended = self._is_finger_extended(landmarks, 20, 18, 17)
        
        # Check for pointing gesture (only index finger extended)
        if not thumb_extended and index_extended and not middle_extended and not ring_extended and not pinky_extended:
            # Determine pointing direction
            return self._get_pointing_direction(landmarks)
        
        # Check for open palm (all fingers extended)
        if thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended:
            return "open_palm"
        
        return "unknown"
    
    def update_gesture(self, hand_landmarks):
        """Update current gesture with smoothing"""
        gesture = self.recognize_gesture(hand_landmarks)
        
        # Add to buffer
        self.gesture_buffer.append(gesture)
        if len(self.gesture_buffer) > self.buffer_size:
            self.gesture_buffer.pop(0)
        
        # Find most common gesture in buffer
        if self.gesture_buffer:
            # Count occurrences of each gesture
            gesture_counts = {}
            for g in self.gesture_buffer:
                if g in gesture_counts:
                    gesture_counts[g] += 1
                else:
                    gesture_counts[g] = 1
            
            # Find the most common gesture
            most_common = max(gesture_counts.items(), key=lambda x: x[1])
            
            # Only update if the gesture appears more than 50% of the time in the buffer
            if most_common[1] > len(self.gesture_buffer) / 2:
                self.current_gesture = most_common[0]
        
        return self.current_gesture
    
    def get_command(self, gesture=None):
        """Convert gesture to command"""
        if gesture is None:
            gesture = self.current_gesture
        
        return self.gestures.get(gesture, "No Action")
    
    def _is_thumb_extended(self, landmarks):
        """Check if thumb is extended"""
        # Thumb is extended if the tip is to the right/left of the IP joint
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        
        # Calculate the vector from MCP to IP
        vec_mcp_ip = (thumb_ip.x - thumb_mcp.x, thumb_ip.y - thumb_mcp.y)
        # Calculate the vector from IP to tip
        vec_ip_tip = (thumb_tip.x - thumb_ip.x, thumb_tip.y - thumb_ip.y)
        
        # Calculate the dot product to see if they point in the same direction
        dot_product = vec_mcp_ip[0] * vec_ip_tip[0] + vec_mcp_ip[1] * vec_ip_tip[1]
        return dot_product > 0
    
    def _is_finger_extended(self, landmarks, tip_id, pip_id, mcp_id):
        """Check if a finger is extended by comparing the Y coordinates"""
        tip = landmarks[tip_id]
        pip = landmarks[pip_id]
        mcp = landmarks[mcp_id]
        
        # Calculate the length of the finger
        finger_length = self._distance_3d(mcp, pip) + self._distance_3d(pip, tip)
        
        # Calculate direct distance from MCP to tip
        direct_distance = self._distance_3d(mcp, tip)
        
        # If the direct distance is close to the finger length, the finger is extended
        # Use a threshold to allow some flexibility
        ratio = direct_distance / finger_length if finger_length > 0 else 0
        return ratio > 0.7  # Threshold can be adjusted
    
    def _get_pointing_direction(self, landmarks):
        """Determine the direction of pointing (up, down, left, right)"""
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        
        # Calculate the vector from PIP to tip
        dx = index_tip.x - index_pip.x
        dy = index_tip.y - index_pip.y
        
        # Determine the primary direction
        if abs(dx) > abs(dy):
            # Horizontal pointing
            return "point_right" if dx > 0 else "point_left"
        else:
            # Vertical pointing
            return "point_up" if dy < 0 else "point_down"
    
    def _distance_3d(self, landmark1, landmark2):
        """Calculate 3D distance between landmarks"""
        return math.sqrt(
            (landmark1.x - landmark2.x)**2 +
            (landmark1.y - landmark2.y)**2 +
            (landmark1.z - landmark2.z)**2
        )