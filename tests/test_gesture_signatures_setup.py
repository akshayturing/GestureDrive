# test_gesture_signatures_setup.py
import os
import shutil
import json
import tempfile
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

class TestSetup:
    """Provides setup and teardown utilities for gesture signature tests"""
    
    @classmethod
    def create_temp_dirs(cls):
        """Create temporary directories for testing"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.models_dir = os.path.join(cls.temp_dir, "models")
        cls.training_dir = os.path.join(cls.temp_dir, "training_data")
        cls.config_dir = os.path.join(cls.temp_dir, "config")
        cls.cache_dir = os.path.join(cls.temp_dir, "signature_cache")
        
        # Create directories
        os.makedirs(cls.models_dir, exist_ok=True)
        os.makedirs(cls.training_dir, exist_ok=True)
        os.makedirs(cls.config_dir, exist_ok=True)
        os.makedirs(cls.cache_dir, exist_ok=True)
        
        return cls.temp_dir
    
    @classmethod
    def cleanup_temp_dirs(cls):
        """Clean up temporary directories after testing"""
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def create_mock_training_session(cls, session_id="test_session", gesture_name="Test Gesture",
                                   example_count=3, frames_per_example=10):
        """Create a mock training session with examples for testing"""
        # Create session directory
        session_dir = os.path.join(cls.training_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Create session metadata
        metadata = {
            "gesture_name": gesture_name,
            "safe_gesture_name": gesture_name.lower().replace(" ", "_"),
            "session_id": session_id,
            "start_time": (datetime.now() - timedelta(hours=1)).timestamp(),
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "required_examples": 5,
            "examples_recorded": example_count,
            "examples": [f"example_{i+1:02d}.json" for i in range(example_count)],
            "completed": example_count >= 5
        }
        
        # Save metadata
        with open(os.path.join(session_dir, "session_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Create examples
        examples = []
        
        for i in range(1, example_count+1):
            example_id = f"example_{i:02d}"
            
            # Create example data
            frames = []
            
            for j in range(frames_per_example):
                # Generate random landmark positions for testing
                # We'll create landmarks that move in a circular pattern
                progress = j / frames_per_example
                angle = progress * 2 * np.pi
                
                # Wrist position
                wrist_x = 0.5 + 0.1 * np.cos(angle)
                wrist_y = 0.5 + 0.1 * np.sin(angle)
                
                # Index fingertip position (larger circle)
                index_x = 0.5 + 0.25 * np.cos(angle)
                index_y = 0.5 + 0.25 * np.sin(angle)
                
                # Create landmarks for a simplified hand (just wrist and index finger)
                landmarks = [
                    [wrist_x, wrist_y, 0.0],  # Wrist
                    [0.5, 0.5, 0.0],  # Thumb CMC
                    [(wrist_x + index_x)/2, (wrist_y + index_y)/2, 0.0],  # Index MCP
                    [(wrist_x + 2*index_x)/3, (wrist_y + 2*index_y)/3, 0.0],  # Index PIP
                    [index_x, index_y, 0.0]  # Index tip
                ]
                
                # Frame timestamp
                timestamp = datetime.now().timestamp() - (frames_per_example - j) * 0.1
                
                # Add frame
                frames.append({
                    "timestamp": timestamp,
                    "landmarks": landmarks,
                    "handedness": "Right"
                })
            
            # Create example
            example = {
                "example_id": example_id,
                "gesture_name": gesture_name,
                "start_time": frames[0]["timestamp"] - 0.1,
                "end_time": frames[-1]["timestamp"] + 0.1,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "frames": frames,
                "duration_seconds": frames[-1]["timestamp"] - frames[0]["timestamp"],
                "frame_count": len(frames),
                "quality_check": {
                    "is_valid": True,
                    "frame_count": len(frames),
                    "duration_seconds": frames[-1]["timestamp"] - frames[0]["timestamp"]
                }
            }
            
            # Save example
            with open(os.path.join(session_dir, f"{example_id}.json"), "w") as f:
                json.dump(example, f, indent=2)
            
            examples.append(example)
        
        # Create training data file
        training_data = {
            "gesture_name": gesture_name,
            "created": datetime.now().isoformat(),
            "example_count": example_count,
            "examples": examples
        }
        
        # Save training data
        training_data_path = os.path.join(session_dir, "training_data.json")
        with open(training_data_path, "w") as f:
            json.dump(training_data, f, indent=2)
        
        return training_data_path
    
    @classmethod
    def create_mock_landmarks(cls, pattern="circle", frames=30):
        """Create mock hand landmarks for testing"""
        landmarks_sequence = []
        timestamps = []
        
        for i in range(frames):
            progress = i / frames
            
            if pattern == "circle":
                # Circular pattern
                angle = progress * 2 * np.pi
                
                # Wrist position
                wrist_x = 0.5 + 0.1 * np.cos(angle)
                wrist_y = 0.5 + 0.1 * np.sin(angle)
                
                # Index fingertip position (larger circle)
                index_x = 0.5 + 0.25 * np.cos(angle)
                index_y = 0.5 + 0.25 * np.sin(angle)
                
            elif pattern == "swipe_right":
                # Horizontal swipe pattern
                wrist_x = 0.3 + progress * 0.4
                wrist_y = 0.5
                index_x = 0.2 + progress * 0.6
                index_y = 0.5 - 0.1 * np.sin(progress * np.pi)  # Small arc
                
            elif pattern == "swipe_down":
                # Vertical swipe pattern
                wrist_x = 0.5
                wrist_y = 0.3 + progress * 0.4
                index_x = 0.5 + 0.1 * np.sin(progress * np.pi)  # Small arc
                index_y = 0.2 + progress * 0.6
                
            else:  # Default to random movement
                wrist_x = 0.5 + 0.1 * np.sin(progress * 4 * np.pi)
                wrist_y = 0.5 + 0.1 * np.cos(progress * 4 * np.pi)
                index_x = 0.5 + 0.2 * np.cos(progress * 6 * np.pi)
                index_y = 0.5 + 0.2 * np.sin(progress * 6 * np.pi)
            
            # Create landmarks for a simplified hand (just wrist and index finger)
            landmarks = [
                [wrist_x, wrist_y, 0.0],  # Wrist
                [0.5, 0.5, 0.0],  # Thumb CMC
                [(wrist_x + index_x)/2, (wrist_y + index_y)/2, 0.0],  # Index MCP
                [(wrist_x + 2*index_x)/3, (wrist_y + 2*index_y)/3, 0.0],  # Index PIP
                [index_x, index_y, 0.0]  # Index tip
            ]
            
            landmarks_sequence.append(landmarks)
            timestamps.append(datetime.now().timestamp() - (frames - i) * 0.1)
        
        return landmarks_sequence, timestamps
    
    @classmethod
    def create_mock_signature(cls, gesture_name="Test Gesture"):
        """Create a mock gesture signature for testing"""
        # Create trajectories for key landmarks
        wrist_trajectory = []
        index_trajectory = []
        
        for i in range(20):
            progress = i / 19
            angle = progress * 2 * np.pi
            
            wrist_x = 0.5 + 0.1 * np.cos(angle)
            wrist_y = 0.5 + 0.1 * np.sin(angle)
            wrist_trajectory.append([wrist_x, wrist_y, 0.0])
            
            index_x = 0.5 + 0.25 * np.cos(angle)
            index_y = 0.5 + 0.25 * np.sin(angle)
            index_trajectory.append([index_x, index_y, 0.0])
        
        # Create mock signature
        signature = {
            "gesture_name": gesture_name,
            "created": datetime.now().isoformat(),
            "source": "test_training_data.json",
            "example_count": 3,
            "example_signatures": [
                {
                    "example_id": "example_01",
                    "frame_count": 10,
                    "duration": 1.0,
                    "trajectories": {
                        "landmark_0": wrist_trajectory,
                        "landmark_4": index_trajectory
                    },
                    "velocities": [],
                    "accelerations": [],
                    "hand_shapes": [],
                    "feature_vectors": {
                        "trajectory_features": {
                            "landmark_0": {
                                "path_length": 0.628,
                                "displacement": 0.01,
                                "straightness": 0.016,
                                "mean_curvature": 0.314,
                                "area": 0.0314
                            },
                            "landmark_4": {
                                "path_length": 1.57,
                                "displacement": 0.02,
                                "straightness": 0.013,
                                "mean_curvature": 0.314,
                                "area": 0.196
                            }
                        },
                        "velocity_features": {
                            "landmark_0": {
                                "mean_speed": 0.628,
                                "max_speed": 0.628,
                                "direction_consistency": 0.0
                            },
                            "landmark_4": {
                                "mean_speed": 1.57,
                                "max_speed": 1.57,
                                "direction_consistency": 0.0
                            }
                        }
                    }
                }
            ],
            "feature_vectors": {
                "trajectory_features": {
                    "landmark_0": {
                        "path_length": 0.628,
                        "displacement": 0.01,
                        "straightness": 0.016,
                        "mean_curvature": 0.314,
                        "area": 0.0314
                    },
                    "landmark_4": {
                        "path_length": 1.57,
                        "displacement": 0.02,
                        "straightness": 0.013,
                        "mean_curvature": 0.314,
                        "area": 0.196
                    }
                },
                "velocity_features": {
                    "landmark_0": {
                        "mean_speed": 0.628,
                        "max_speed": 0.628,
                        "direction_consistency": 0.0
                    },
                    "landmark_4": {
                        "mean_speed": 1.57,
                        "max_speed": 1.57,
                        "direction_consistency": 0.0
                    }
                }
            },
            "pattern_clusters": {
                "trajectories": {
                    "landmark_0": wrist_trajectory,
                    "landmark_4": index_trajectory
                }
            },
            "similarity_threshold": 0.75
        }
        
        return signature
    
    @classmethod
    def create_mock_model(cls, gesture_name="Test Gesture"):
        """Create a mock gesture model for testing"""
        signature = cls.create_mock_signature(gesture_name)
        
        model = {
            "gesture_name": gesture_name,
            "created": datetime.now().isoformat(),
            "source_signature": "test_training_data.json",
            "feature_vectors": signature["feature_vectors"],
            "pattern_clusters": signature["pattern_clusters"],
            "recognition_params": {
                "similarity_threshold": 0.75,
                "min_frames": 5,
                "max_frames": 30,
                "feature_weights": {
                    "trajectory": 0.5,
                    "velocity": 0.3,
                    "acceleration": 0.1,
                    "handShape": 0.1
                }
            }
        }
        
        return model
    
    @classmethod
    def create_mock_serialized_gesture(cls, gesture_name="Test Gesture"):
        """Create a mock serialized gesture for testing"""
        signature = cls.create_mock_signature(gesture_name)
        model = cls.create_mock_model(gesture_name)
        
        serialized = {
            "schemaVersion": "1.0",
            "metadata": {
                "gestureName": gesture_name,
                "created": datetime.now().isoformat(),
                "lastModified": datetime.now().isoformat(),
                "author": "Test User",
                "description": f"Test gesture '{gesture_name}'",
                "tags": ["test", "circle"],
                "trainingSource": {
                    "sessionId": "test_session",
                    "exampleCount": 3,
                    "totalFrames": 30
                }
            },
            "signature": {
                "trajectoryFeatures": signature["feature_vectors"]["trajectory_features"],
                "velocityFeatures": signature["feature_vectors"]["velocity_features"],
                "accelerationFeatures": {},
                "handShapeFeatures": {},
                "patternClusters": signature["pattern_clusters"]
            },
            "recognitionParams": {
                "similarityThreshold": 0.75,
                "minFrames": 5,
                "maxFrames": 30,
                "temporalWindow": 20,
                "cooldownFrames": 10,
                "featureWeights": {
                    "trajectory": 0.5,
                    "velocity": 0.3,
                    "acceleration": 0.1,
                    "handShape": 0.1
                }
            },
            "actionMapping": {
                "defaultAction": {
                    "name": gesture_name.lower().replace(" ", "_"),
                    "handler": "custom_gestures.handle_custom_gesture",
                    "description": f"Custom gesture '{gesture_name}'",
                    "params": {
                        "gestureName": gesture_name,
                        "description": f"Custom gesture '{gesture_name}'"
                    }
                },
                "contextualMappings": {
                    "fileBrowser": {
                        "name": "customFileAction",
                        "handler": "file_manager.custom_file_action",
                        "description": f"Custom file action for '{gesture_name}'",
                        "params": {
                            "actionType": "select"
                        }
                    }
                }
            }
        }
        
        return serialized