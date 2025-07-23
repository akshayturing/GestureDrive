# mocks.py

class MockLandmark:
    """Mock for MediaPipe landmark."""
    
    def __init__(self, x=0.5, y=0.5, z=0.0):
        self.x = x
        self.y = y
        self.z = z
        
class MockHandLandmarks:
    """Mock for MediaPipe hand landmarks collection."""
    
    def __init__(self, landmark_positions=None):
        """
        Initialize with landmark positions.
        
        Args:
            landmark_positions: List of (x,y,z) tuples for positions,
                               defaults to 21 centered landmarks
        """
        if landmark_positions is None:
            # Default to 21 landmarks at center position
            self.landmark = [MockLandmark() for _ in range(21)]
        else:
            # Use provided positions
            self.landmark = []
            for pos in landmark_positions:
                if len(pos) == 2:
                    self.landmark.append(MockLandmark(pos[0], pos[1]))
                else:
                    self.landmark.append(MockLandmark(pos[0], pos[1], pos[2]))
    
    def set_landmark_position(self, index, x, y, z=0.0):
        """Set position of a specific landmark."""
        if 0 <= index < len(self.landmark):
            self.landmark[index].x = x
            self.landmark[index].y = y
            self.landmark[index].z = z
            
class MockCamera:
    """Mock camera for testing gesture navigation."""
    
    def __init__(self):
        self.hand_landmarks_data = None
        self.frame = None
        self.processed_frame = None
        
    def set_hand_landmarks(self, landmarks=None):
        """Set hand landmarks data."""
        if landmarks is None:
            self.hand_landmarks_data = None
        elif isinstance(landmarks, list):
            # If it's already a list of MockHandLandmarks
            self.hand_landmarks_data = landmarks
        else:
            # Single MockHandLandmarks
            self.hand_landmarks_data = [landmarks]
            
    def create_default_hand(self):
        """Create a default hand with centered landmarks."""
        hand = MockHandLandmarks()
        self.set_hand_landmarks([hand])
        return hand
        
    def get_processed_frame(self):
        """Get the processed frame (mock)."""
        import numpy as np
        if self.processed_frame is None:
            # Create a blank frame if none exists
            self.processed_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        return self.processed_frame.copy()
        
    def stop(self):
        """Stop the camera (mock)."""
        self.hand_landmarks_data = None
        self.frame = None
        self.processed_frame = None
