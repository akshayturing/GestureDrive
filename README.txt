# GestureDrive

## Introduction
This project transforms your webcam into a gesture-based controller for navigating your computer’s file system. Using real-time hand tracking via MediaPipe and OpenCV, users can swipe left to move up a directory, swipe right to enter a folder, and perform other intuitive gestures to interact with files—all without touching a mouse or keyboard.


## Conversations

### 1. Setup Environment & Webcam Feed

Goal: Establish the basic development environment and access the webcam feed.
Install required packages: opencv-python, mediapipe, numpy.
Open webcam stream using OpenCV.
Display live video feed to confirm input.
Save this as a reusable video input module.

### 2. Integrate MediaPipe for Hand Tracking

Goal: Detect hand landmarks in real time using MediaPipe.
Initialize mp.solutions.hands and overlay landmarks on the video.
Track key points (wrist, index fingertip, thumb).
Log coordinates of hand landmarks each frame for debugging.
Confirm tracking works across different lighting and backgrounds.

### 3. Detect Gesture Direction (Left/Right/Up/Down)

Goal: Build logic to detect simple swipe gestures.
Store last 10 frame landmark positions.
Calculate movement vector and speed for gestures.
Implement threshold logic to detect:
Swipe Left → Go back one directory.
Swipe Right → Enter a folder.
Swipe Up/Down → Scroll through directory view.
Add debounce logic to prevent accidental repeated triggers.


### 4. Refinement for gesture handling

Goal: Implement robust directional gesture-based navigation
Track hand movement across the last 10 consecutive frames using landmark positions.
Detect gestures only if movement persists for 500ms or more, reducing false positives.
Validate gesture intent: require all fingers extended (except thumb) and pointing toward camera.
Map gestures to navigation actions:

### 5. Smoother Navigation

Goal: Implement intentional and directional gesture-based navigation refinement
Map swipe directions to actions: up/down for scrolling, left for going back, right for entering folders.
Detect gestures only if motion lasts over 500ms and the hand pose shows all fingers extended (except the thumb), facing forward.
Filter out passive or incidental movement to avoid false triggers.
After executing a gesture, activate a cooldown period to block repeated actions until a new gesture is clearly detected.

### 6. Implement File selection 

Goal: Enable gesture-based file selection with context-aware actions and safety checks
Detect tap or pinch gestures to initiate file selection via hand movement.
Based on file type:
.txt → Open preview panel
.jpg, .png → Show thumbnail
.pdf → Launch external viewer
Integrate a security layer to restrict access to executables (.exe, .sh, .bat) or system-critical files, ensuring safe navigation.

### 7. Optimize with Custom Gesture Profiles

Goal: Make the system extensible and responsive to user preferences.
Create a config file (JSON) to map gestures to actions.
Allow user to define custom gesture-action pairs (e.g., “Swipe Down + Hold” → Delete file).
Optionally train gestures via webcam and save their profile.
Add replay mode or tutorial using stored gesture logs.


### 8. Optimize, Debug, Refactor, and Expand Unit Tests

Associate swipe directions with navigation actions: up/down to scroll, left to go back, right to enter a folder.
Recognize gestures only if they persist for over 500ms with correct hand pose—all fingers extended except the thumb, facing the camera.
After executing a gesture, trigger a cooldown period to block repeated inputs until a new deliberate gesture is detected.

## Code Execution Screenshots
### Conversation 1: Execution Output
![Conversation 1 Execution](https://drive.google.com/file/d/1LYLy9d6lchiJwdmowk1Ewl1TRamdbyxk/view?usp=drive_link)
### Conversation 2: Execution Output
![Conversation 2 Execution](https://drive.google.com/file/d/1XNPSg1xRU2voghVacyLsxKrk8e425pUt/view?usp=drive_link)
### Conversation 3: Execution Output
![Conversation 3 Execution](https://drive.google.com/file/d/1k5lB0rr3JRcU1K0XWcBOlru6DUhAaAfZ/view?usp=drive_link)
### Conversation 4: Execution Output
![Conversation 4 Execution](https://drive.google.com/file/d/1Ax_bmtMkGzA3k0NdsjO3s2s46IsTxInN/view?usp=drive_link)
### Conversation 5: Execution Output
![Conversation 5 Execution](https://drive.google.com/file/d/1qUkNjsPuA5NwPRiu2ZlXxVCjXLOFCw01/view?usp=drive_link)
### Conversation 6: Execution Output
![Conversation 6 Execution](https://drive.google.com/file/d/1WZJqdflPGFcYMOAzDjcoUeP6cwmXiD1S/view?usp=drive_link)
### Conversation 7: Execution Output
![Conversation 7 Execution](https://drive.google.com/file/d/10hpfh3Qy3lLBISZcOd_wlBU_C-LnYS-G/view?usp=drive_link)
### Conversation 8: Execution Output
![Conversation 8 Execution](https://drive.google.com/file/d/1GMMGbcOZMlqJ-qCpfMK0tQ-qbcNi37k0/view?usp=drive_link)


## Unit Test Outputs and Coverage
The following test cases validate critical components of the system.
### Conversation 1 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1vUzFmATfTuMzuRE9rOwJGzjrivgHVwWB/view?usp=drive_link)

### Conversation 2 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1y979rMLHXE-7JbfVqmKgDva3aJmG6bqJ/view?usp=drive_link)

### Conversation 3 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1RcTrdX6Kby_ojI1C428Yphpzitl4y8fV/view?usp=drive_link)

### Conversation 4 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1CU2jmIoFZQ79sOkWHaJXamnC3_A9UWcr/view?usp=drive_link)

### Conversation 5 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1_Lb1pbE1MnzCA32qq2uQgCo8TMC06_8E/view?usp=drive_link)

### Conversation 6 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1yd1jEsYA8IwTzRvB7go2QZfNRXd3MuPY/view?usp=drive_link)

### Conversation 7 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1kpPQMn3_HWTLCsIiMAWnf-j5xNk8xRSX/view?usp=drive_link)

### Conversation 8 Test Results
- **Test 1**: 
  ![Test 1](https://drive.google.com/file/d/1p_jg2bTgbd6DESfiGOgB1Elhoh9zWL3c/view?usp=drive_link)
- **Test 2**:
  ![Test 2](https://drive.google.com/file/d/1U8a_uP5Q61UVNJMSSwyC3KYOS4FXpDRl/view?usp=drive_link)
