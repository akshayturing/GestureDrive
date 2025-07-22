# hand_motion_analyzer.py
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import logging
from scipy import signal
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from dtw import dtw
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HandMotionAnalyzer:
    """
    Analyzes hand motion data to extract features, detect patterns,
    and compare motion sequences.
    """
    
    def __init__(self):
        """Initialize the HandMotionAnalyzer"""
        logger.info("HandMotionAnalyzer initialized")
    
    def extract_trajectory(self, recording: Dict, landmark_index: int = 8, 
                          hand_index: int = 0) -> np.ndarray:
        """
        Extract the trajectory of a specific landmark from a recording.
        
        Args:
            recording: The recording dictionary
            landmark_index: Index of the landmark to track (default: 8 = index fingertip)
            hand_index: Which hand to use if multiple are present
            
        Returns:
            Array of [x, y, z] positions over time
        """
        trajectory = []
        
        for frame in recording.get("frames", []):
            hands = frame.get("hands", [])
            if hand_index < len(hands):
                hand = hands[hand_index]
                landmarks = hand.get("landmarks", [])
                
                if landmark_index < len(landmarks):
                    trajectory.append(landmarks[landmark_index])
        
        return np.array(trajectory)
    
    def extract_velocity_profile(self, recording: Dict, landmark_index: int = 8, 
                               hand_index: int = 0) -> np.ndarray:
        """
        Extract the velocity profile of a specific landmark from a recording.
        
        Args:
            recording: The recording dictionary
            landmark_index: Index of the landmark to track
            hand_index: Which hand to use if multiple are present
            
        Returns:
            Array of velocity magnitudes over time
        """
        velocities = []
        
        for frame in recording.get("frames", []):
            hands = frame.get("hands", [])
            if hand_index < len(hands):
                hand = hands[hand_index]
                vels = hand.get("velocities", [])
                
                if landmark_index < len(vels):
                    velocities.append(vels[landmark_index].get("magnitude", 0))
        
        return np.array(velocities)
    
    def detect_gestures(self, recording: Dict, 
                       velocity_threshold: float = 1.0,
                       min_gesture_frames: int = 5) -> List[Dict]:
        """
        Detect potential gestures in a recording based on velocity patterns.
        
        Args:
            recording: The recording dictionary
            velocity_threshold: Minimum velocity to consider as gesture movement
            min_gesture_frames: Minimum frames for a gesture
            
        Returns:
            List of detected gesture segments with start/end indices
        """
        gestures = []
        
        # Extract average velocity magnitude for each frame
        avg_velocities = []
        
        for frame in recording.get("frames", []):
            hands = frame.get("hands", [])
            if not hands:
                avg_velocities.append(0)
                continue
                
            # Average velocity across all landmarks in the first hand
            hand = hands[0]
            vels = hand.get("velocities", [])
            if not vels:
                avg_velocities.append(0)
                continue
                
            avg_vel = sum(v.get("magnitude", 0) for v in vels) / len(vels)
            avg_velocities.append(avg_vel)
        
        # Smooth velocities to reduce noise
        if avg_velocities:
            avg_velocities = signal.savgol_filter(avg_velocities, 5, 2)
        
        # Detect segments with high velocity (potential gestures)
        in_gesture = False
        start_idx = 0
        
        for i, vel in enumerate(avg_velocities):
            if not in_gesture and vel > velocity_threshold:
                # Start of potential gesture
                in_gesture = True
                start_idx = i
            elif in_gesture and vel < velocity_threshold:
                # End of potential gesture
                if (i - start_idx) >= min_gesture_frames:
                    gestures.append({
                        "start_frame": start_idx,
                        "end_frame": i,
                        "duration_frames": i - start_idx,
                        "avg_velocity": np.mean(avg_velocities[start_idx:i])
                    })
                in_gesture = False
        
        # Handle gesture that continues until the end
        if in_gesture and (len(avg_velocities) - start_idx) >= min_gesture_frames:
            gestures.append({
                "start_frame": start_idx,
                "end_frame": len(avg_velocities),
                "duration_frames": len(avg_velocities) - start_idx,
                "avg_velocity": np.mean(avg_velocities[start_idx:])
            })
        
        return gestures
    
    def compare_trajectories(self, traj1: np.ndarray, traj2: np.ndarray) -> Dict:
        """
        Compare two hand motion trajectories using Dynamic Time Warping.
        
        Args:
            traj1: First trajectory array
            traj2: Second trajectory array
            
        Returns:
            Dictionary with comparison metrics
        """
        # Ensure trajectories are numpy arrays
        traj1 = np.array(traj1)
        traj2 = np.array(traj2)
        
        # Normalize the trajectories to account for different coordinate systems
        traj1_norm = traj1 - np.mean(traj1, axis=0)
        traj2_norm = traj2 - np.mean(traj2, axis=0)
        
        # Ensure same dimensionality
        if traj1_norm.shape[1] != traj2_norm.shape[1]:
            min_dim = min(traj1_norm.shape[1], traj2_norm.shape[1])
            traj1_norm = traj1_norm[:, :min_dim]
            traj2_norm = traj2_norm[:, :min_dim]
        
        # Compute DTW distance
        d, cost_matrix, acc_cost_matrix, path = dtw(traj1_norm, traj2_norm, dist=lambda x, y: np.linalg.norm(x - y))
        
        # Calculate path length and ratio to direct path
        path_length = len(path[0])
        direct_path_length = max(len(traj1_norm), len(traj2_norm))
        path_ratio = path_length / direct_path_length if direct_path_length > 0 else 1.0
        
        # Calculate similarity score (inversely related to distance)
        max_distance = np.sqrt(traj1_norm.shape[1])  # Maximum possible distance in normalized space
        similarity = 1.0 / (1.0 + d/max_distance)
        
        return {
            "dtw_distance": d,
            "path_length": path_length,
            "path_ratio": path_ratio,
            "similarity_score": similarity,
            "alignment_path": path
        }
    
    def extract_features(self, recording: Dict, hand_index: int = 0) -> Dict:
        """
        Extract meaningful features from a hand motion recording.
        
        Args:
            recording: The recording dictionary
            hand_index: Which hand to use if multiple are present
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Extract trajectories for key landmarks
        key_landmarks = {
            "wrist": 0,
            "thumb_tip": 4,
            "index_tip": 8,
            "middle_tip": 12,
            "ring_tip": 16,
            "pinky_tip": 20
        }
        
        trajectories = {}
        for name, landmark_index in key_landmarks.items():
            trajectories[name] = self.extract_trajectory(recording, landmark_index, hand_index)
        
        # Calculate total distance traveled for each landmark
        features["total_distance"] = {}
        for name, trajectory in trajectories.items():
            if len(trajectory) >= 2:
                diffs = np.diff(trajectory, axis=0)
                distances = np.sqrt(np.sum(diffs**2, axis=1))
                features["total_distance"][name] = np.sum(distances)
        
        # Calculate average velocity
        features["avg_velocity"] = {}
        for name, landmark_index in key_landmarks.items():
            vel_profile = self.extract_velocity_profile(recording, landmark_index, hand_index)
            if len(vel_profile) > 0:
                features["avg_velocity"][name] = np.mean(vel_profile)
        
        # Calculate bounding box
        all_points = np.vstack([traj for traj in trajectories.values() if len(traj) > 0])
        if len(all_points) > 0:
            features["bounding_box"] = {
                "min_x": np.min(all_points[:, 0]),
                "max_x": np.max(all_points[:, 0]),
                "min_y": np.min(all_points[:, 1]),
                "max_y": np.max(all_points[:, 1]),
                "width": np.max(all_points[:, 0]) - np.min(all_points[:, 0]),
                "height": np.max(all_points[:, 1]) - np.min(all_points[:, 1])
            }
        
        # Calculate smoothness (using normalized jerk)
        features["smoothness"] = {}
        for name, trajectory in trajectories.items():
            if len(trajectory) >= 3:
                # Calculate velocities and accelerations
                velocities = np.diff(trajectory, axis=0)
                accelerations = np.diff(velocities, axis=0)
                
                # Calculate jerk (derivative of acceleration)
                jerk = np.diff(accelerations, axis=0)
                
                # Normalized jerk
                if len(jerk) > 0:
                    jerk_magnitude = np.sqrt(np.sum(jerk**2, axis=1))
                    features["smoothness"][name] = np.mean(jerk_magnitude)
        
        # Detect potential gestures
        features["gestures"] = self.detect_gestures(recording)
        
        # Calculate gesture frequency
        if len(features["gestures"]) > 0:
            duration = recording.get("metadata", {}).get("duration_seconds", 0)
            if duration > 0:
                features["gesture_frequency"] = len(features["gestures"]) / duration
        
        return features
    
    def visualize_trajectory(self, trajectory: np.ndarray, 
                           title: str = "Hand Motion Trajectory",
                           ax: Optional[Axes] = None,
                           show: bool = True) -> Optional[Tuple[Figure, Axes]]:
        """
        Visualize a hand motion trajectory in 3D.
        
        Args:
            trajectory: Numpy array of shape (n_frames, 3) with x, y, z coordinates
            title: Plot title
            ax: Optional matplotlib axis to plot on
            show: Whether to show the plot (if False, returns figure and axes)
            
        Returns:
            Tuple of (figure, axes) if show=False, otherwise None
        """
        if len(trajectory) == 0:
            logger.warning("Empty trajectory, nothing to visualize.")
            return None
        
        # Create new figure if not provided
        if ax is None:
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
        else:
            fig = ax.figure
        
        # Plot trajectory
        xs, ys, zs = trajectory[:, 0], trajectory[:, 1], trajectory[:, 2]
        
        # Plot line with colormap representing time
        points = ax.scatter(xs, ys, zs, c=range(len(xs)), cmap='viridis', 
                          s=10, alpha=0.8, label='Motion Path')
        
        # Plot line connecting points
        ax.plot(xs, ys, zs, 'gray', alpha=0.5, linewidth=1)
        
        # Mark start and end points
        ax.scatter(xs[0], ys[0], zs[0], color='green', s=100, label='Start')
        ax.scatter(xs[-1], ys[-1], zs[-1], color='red', s=100, label='End')
        
        # Add colorbar
        cbar = plt.colorbar(points, ax=ax, pad=0.1)
        cbar.set_label('Time (frames)')
        
        # Set labels and title
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title(title)
        
        # Add legend
        ax.legend()
        
        # Show equal aspect ratio
        max_range = np.max([
            np.ptp(xs), np.ptp(ys), np.ptp(zs)
        ])
        
        mid_x = np.mean([np.min(xs), np.max(xs)])
        mid_y = np.mean([np.min(ys), np.max(ys)])
        mid_z = np.mean([np.min(zs), np.max(zs)])
        
        ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
        ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
        ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
        
        if show:
            plt.tight_layout()
            plt.show()
            return None
        else:
            return fig, ax
    
    def visualize_velocity_profile(self, recording: Dict, landmark_index: int = 8,
                                 hand_index: int = 0, title: str = "Velocity Profile",
                                 ax: Optional[Axes] = None,
                                 show: bool = True) -> Optional[Tuple[Figure, Axes]]:
        """
        Visualize the velocity profile of a hand motion.
        
        Args:
            recording: The recording dictionary
            landmark_index: Index of the landmark to analyze
            hand_index: Which hand to use if multiple are present
            title: Plot title
            ax: Optional matplotlib axis to plot on
            show: Whether to show the plot
            
        Returns:
            Tuple of (figure, axes) if show=False, otherwise None
        """
        # Extract velocity profile
        velocity_profile = self.extract_velocity_profile(recording, landmark_index, hand_index)
        
        if len(velocity_profile) == 0:
            logger.warning("Empty velocity profile, nothing to visualize.")
            return None
        
        # Create new figure if not provided
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        # Plot velocity profile
        ax.plot(velocity_profile, linewidth=2, color='blue')
        
        # Add smoothed version
        if len(velocity_profile) > 5:
            smoothed = signal.savgol_filter(velocity_profile, min(11, len(velocity_profile) // 2 * 2 + 1), 3)
            ax.plot(smoothed, linewidth=2, color='red', alpha=0.7, label='Smoothed')
        
        # Add horizontal lines for common thresholds
        ax.axhline(y=0.5, color='green', linestyle='--', alpha=0.5, label='Slow Motion')
        ax.axhline(y=1.0, color='orange', linestyle='--', alpha=0.5, label='Medium Motion')
        ax.axhline(y=2.0, color='red', linestyle='--', alpha=0.5, label='Fast Motion')
        
        # Set labels and title
        ax.set_xlabel('Frame')
        ax.set_ylabel('Velocity Magnitude')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        if show:
            plt.tight_layout()
            plt.show()
            return None
        else:
            return fig, ax
    
    def visualize_motion_heatmap(self, recording: Dict, resolution: Tuple[int, int] = (50, 50),
                               hand_index: int = 0, show: bool = True) -> Optional[Tuple[Figure, Axes]]:
        """
        Generate a heatmap of hand motion density.
        
        Args:
            recording: The recording dictionary
            resolution: Bin resolution for the heatmap
            hand_index: Which hand to use if multiple are present
            show: Whether to show the plot
            
        Returns:
            Tuple of (figure, axes) if show=False, otherwise None
        """
        # Extract positions of all landmarks
        positions = []
        
        for frame in recording.get("frames", []):
            hands = frame.get("hands", [])
            if hand_index < len(hands):
                hand = hands[hand_index]
                landmarks = hand.get("landmarks", [])
                
                # Add all landmark positions
                for lm in landmarks:
                    positions.append((lm[0], lm[1]))  # x, y positions
        
        if not positions:
            logger.warning("No positions found, cannot generate heatmap.")
            return None
            
        # Convert to numpy array
        positions = np.array(positions)
        
        # Create histogram
        heatmap, xedges, yedges = np.histogram2d(
            positions[:, 0], positions[:, 1], bins=resolution
        )
        
        # Create new figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot heatmap
        im = ax.imshow(heatmap.T, origin='lower', 
                      extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]],
                      cmap='viridis', aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Frequency')
        
        # Set labels and title
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_title('Hand Motion Density Heatmap')
        
        if show:
            plt.tight_layout()
            plt.show()
            return None
        else:
            return fig, ax
