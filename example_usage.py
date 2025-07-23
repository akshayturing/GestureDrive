# example_usage.py
import cv2
import numpy as np
import os
from hand_motion_recorder import HandMotionRecorder
from hand_motion_analyzer import HandMotionAnalyzer
from hand_motion_visualizer import HandMotionVisualizer
from hand_motion_player import HandMotionPlayer
from hand_motion_dataset import HandMotionDataset

def test_hand_motion_recording_and_analysis():
    # 1. Create a recorder and record hand motions
    print("\n===== Recording Hand Motions =====")
    recorder = HandMotionRecorder(record_dir="recordings")
    recording_path = recorder.run_recording_session(
        duration_seconds=10, 
        label="circle_gesture",
        display=True  # Show camera feed during recording
    )
    
    if not recording_path:
        print("Recording failed or was cancelled.")
        return
    print(f"Recording saved to: {recording_path}")
    
    # 2. Create an analyzer and process the recording
    print("\n===== Analyzing Recording =====")
    analyzer = HandMotionAnalyzer()
    recording = recorder.load_recording(recording_path)
    
    # Extract features
    features = analyzer.extract_features(recording)
    print(f"Extracted {len(features)} feature groups")
    
    # Detect gestures
    gestures = analyzer.detect_gestures(recording)
    print(f"Detected {len(gestures)} potential gestures")
    
    # 3. Visualize the recording
    print("\n===== Visualizing Recording =====")
    visualizer = HandMotionVisualizer()
    
    # Visualize the trajectory in 3D
    index_finger_trajectory = analyzer.extract_trajectory(recording, landmark_index=8)
    visualizer.visualize_trajectory(index_finger_trajectory, title="Index Finger Trajectory")
    
    # Visualize velocity profile
    visualizer.visualize_velocity_profile(recording, landmark_index=8, 
                                        title="Index Finger Velocity Profile")
    
    # Generate motion heatmap
    heatmap = visualizer.generate_motion_heatmap(recording)
    cv2.imshow("Motion Heatmap", heatmap)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    # 4. Play back the recording
    print("\n===== Playing Recording =====")
    player = HandMotionPlayer(visualizer)
    player.set_recording(recording)
    player.play_interactive()
    
    # 5. Add to dataset
    print("\n===== Managing Dataset =====")
    dataset = HandMotionDataset(dataset_dir="datasets")
    
    # Create a new dataset if it doesn't exist
    datasets = dataset.list_datasets()
    if not any(d["name"] == "GestureExamples" for d in datasets):
        dataset.create_dataset("GestureExamples", "Example hand gesture recordings")
    else:
        dataset.load_dataset("GestureExamples")
    
    # Add the recording to the dataset
    dataset.add_recording(recording_path, label="circle_gesture")
    
    # Extract features for all recordings in the dataset
    features = dataset.extract_features(regenerate=True)
    
    # Export features to CSV
    csv_path = dataset.export_features_csv()
    if csv_path:
        print(f"Exported features to: {csv_path}")

if __name__ == "__main__":
    test_hand_motion_recording_and_analysis()
