import cv2
import mediapipe as mp
import numpy as np
from flask import Flask

# Test OpenCV
print(f"OpenCV version: {cv2.__version__}")

# Test MediaPipe
mp_hands = mp.solutions.hands
print(f"MediaPipe version: {mp.__version__}")

# Test NumPy
print(f"NumPy version: {np.__version__}")

# Test Flask
app = Flask(__name__)
print(f"Flask version: {Flask.__version__}")

print("All libraries imported successfully!")

# Test webcam access
try:
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        print("Webcam access successful!")
    else:
        print("Could not read from webcam.")
    cap.release()
except Exception as e:
    print(f"Webcam access error: {e}")