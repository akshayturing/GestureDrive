# hand_motion_dataset.py
import os
import json
import glob
import shutil
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import pandas as pd
from hand_motion_analyzer import HandMotionAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HandMotionDataset:
    """
    Manages collections of hand motion recordings, with support for
    organizing, labeling, searching, and exporting datasets for analysis or training.
    """
    
    def __init__(self, dataset_dir: str = "datasets"):
        """
        Initialize the HandMotionDataset.
        
        Args:
            dataset_dir: Directory to store datasets
        """
        self.dataset_dir = dataset_dir
        self.analyzer = HandMotionAnalyzer()
        
        # Ensure dataset directory exists
        os.makedirs(dataset_dir, exist_ok=True)
        
        # Current active dataset
        self.active_dataset = None
        self.active_dataset_path = None
        
        logger.info("HandMotionDataset initialized")
    
    def create_dataset(self, name: str, description: str = "") -> bool:
        """
        Create a new dataset.
        
        Args:
            name: Name of the dataset
            description: Description of the dataset
            
        Returns:
            True if successful, False otherwise
        """
        # Sanitize dataset name (only alphanumeric chars and underscores)
        safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        
        # Create dataset directory
        dataset_path = os.path.join(self.dataset_dir, safe_name)
        
        if os.path.exists(dataset_path):
            logger.error(f"Dataset '{name}' already exists")
            return False
            
        try:
            # Create directory structure
            os.makedirs(dataset_path)
            os.makedirs(os.path.join(dataset_path, 'recordings'))
            
            # Create metadata file
            metadata = {
                "name": name,
                "description": description,
                "created": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "recording_count": 0,
                "labels": [],
                "features": {}
            }
            
            with open(os.path.join(dataset_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.info(f"Created dataset '{name}' at {dataset_path}")
            
            # Set as active dataset
            self.active_dataset = metadata
            self.active_dataset_path = dataset_path
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating dataset: {str(e)}")
            return False
    
    def load_dataset(self, name: str) -> bool:
        """
        Load an existing dataset.
        
        Args:
            name: Name of the dataset to load
            
        Returns:
            True if successful, False otherwise
        """
        dataset_path = os.path.join(self.dataset_dir, name)
        metadata_path = os.path.join(dataset_path, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            logger.error(f"Dataset '{name}' not found at {dataset_path}")
            return False
            
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            self.active_dataset = metadata
            self.active_dataset_path = dataset_path
            
            logger.info(f"Loaded dataset '{name}' with {metadata.get('recording_count', 0)} recordings")
            return True
            
        except Exception as e:
            logger.error(f"Error loading dataset: {str(e)}")
            return False
    
    def list_datasets(self) -> List[Dict]:
        """
        List all available datasets.
        
        Returns:
            List of dataset metadata dictionaries
        """
        datasets = []
        
        for item in os.listdir(self.dataset_dir):
            item_path = os.path.join(self.dataset_dir, item)
            metadata_path = os.path.join(item_path, 'metadata.json')
            
            if os.path.isdir(item_path) and os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        
                    # Add recording count
                    recordings_dir = os.path.join(item_path, 'recordings')
                    recording_count = len(glob.glob(os.path.join(recordings_dir, '*.json')))
                    metadata['recording_count'] = recording_count
                    
                    # Add path info
                    metadata['path'] = item_path
                    
                    datasets.append(metadata)
                    
                except Exception as e:
                    logger.warning(f"Error loading metadata for {item}: {str(e)}")
        
        logger.info(f"Found {len(datasets)} datasets")
        return datasets
    
    def add_recording(self, recording_path: str, label: str = None, move_file: bool = False) -> bool:
        """
        Add a recording to the active dataset.
        
        Args:
            recording_path: Path to the recording JSON file
            label: Optional label for the recording
            move_file: Whether to move the file instead of copying
            
        Returns:
            True if successful, False otherwise
        """
        if not self.active_dataset or not self.active_dataset_path:
            logger.error("No active dataset. Create or load one first.")
            return False
            
        if not os.path.exists(recording_path):
            logger.error(f"Recording file not found: {recording_path}")
            return False
            
        try:
            # Load the recording to extract metadata
            with open(recording_path, 'r') as f:
                recording = json.load(f)
                
            # Extract basic info
            metadata = recording.get('metadata', {})
            
            # Create a filename for the recording in the dataset
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            label_suffix = f"_{label}" if label else ""
            filename = f"recording_{timestamp}{label_suffix}.json"
            
            # Destination path in the dataset
            dest_path = os.path.join(self.active_dataset_path, 'recordings', filename)
            
            # Copy or move the file
            if move_file:
                shutil.move(recording_path, dest_path)
            else:
                shutil.copy2(recording_path, dest_path)
                
            # Update the recording metadata
            if label and 'metadata' in recording:
                recording['metadata']['label'] = label
                
                # Save the updated recording
                with open(dest_path, 'w') as f:
                    json.dump(recording, f, indent=2)
            
            # Update dataset metadata
            self.active_dataset['recording_count'] = self.active_dataset.get('recording_count', 0) + 1
            self.active_dataset['last_modified'] = datetime.now().isoformat()
            
            # Add label to dataset labels if new
            if label and label not in self.active_dataset.get('labels', []):
                if 'labels' not in self.active_dataset:
                    self.active_dataset['labels'] = []
                self.active_dataset['labels'].append(label)
            
            # Save updated dataset metadata
            with open(os.path.join(self.active_dataset_path, 'metadata.json'), 'w') as f:
                json.dump(self.active_dataset, f, indent=2)
                
            logger.info(f"Added recording to dataset: {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding recording: {str(e)}")
            return False
    
    def list_recordings(self, label_filter: str = None) -> List[Dict]:
        """
        List all recordings in the active dataset.
        
        Args:
            label_filter: Optional label to filter by
            
        Returns:
            List of recording metadata dictionaries
        """
        if not self.active_dataset or not self.active_dataset_path:
            logger.error("No active dataset. Create or load one first.")
            return []
            
        recordings_dir = os.path.join(self.active_dataset_path, 'recordings')
        recordings = []
        
        for filename in os.listdir(recordings_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(recordings_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        recording = json.load(f)
                        
                    metadata = recording.get('metadata', {})
                    recording_label = metadata.get('label')
                    
                    # Apply label filter if specified
                    if label_filter and recording_label != label_filter:
                        continue
                        
                    # Add file info
                    metadata['filename'] = filename
                    metadata['filepath'] = filepath
                    metadata['frame_count'] = len(recording.get('frames', []))
                    
                    recordings.append(metadata)
                    
                except Exception as e:
                    logger.warning(f"Error loading recording {filename}: {str(e)}")
        
        logger.info(f"Found {len(recordings)} recordings in dataset" + 
                   (f" with label '{label_filter}'" if label_filter else ""))
        
        return recordings
    
    def remove_recording(self, filename: str) -> bool:
        """
        Remove a recording from the active dataset.
        
        Args:
            filename: Filename of the recording to remove
            
        Returns:
            True if successful, False otherwise
        """
        if not self.active_dataset or not self.active_dataset_path:
            logger.error("No active dataset. Create or load one first.")
            return False
            
        filepath = os.path.join(self.active_dataset_path, 'recordings', filename)
        
        if not os.path.exists(filepath):
            logger.error(f"Recording not found: {filepath}")
            return False
            
        try:
            # Read the recording to get its label
            with open(filepath, 'r') as f:
                recording = json.load(f)
                
            label = recording.get('metadata', {}).get('label')
            
            # Remove the file
            os.remove(filepath)
            
            # Update dataset metadata
            self.active_dataset['recording_count'] = max(0, self.active_dataset.get('recording_count', 0) - 1)
            self.active_dataset['last_modified'] = datetime.now().isoformat()
            
            # Remove label from list if no more recordings use it
            if label and label in self.active_dataset.get('labels', []):
                # Check if any other recordings still use this label
                label_still_used = False
                recordings_dir = os.path.join(self.active_dataset_path, 'recordings')
                
                for other_file in os.listdir(recordings_dir):
                    if other_file != filename and other_file.endswith('.json'):
                        other_path = os.path.join(recordings_dir, other_file)
                        try:
                            with open(other_path, 'r') as f:
                                other_rec = json.load(f)
                            other_label = other_rec.get('metadata', {}).get('label')
                            if other_label == label:
                                label_still_used = True
                                break
                        except:
                            continue
                
                if not label_still_used and 'labels' in self.active_dataset:
                    self.active_dataset['labels'].remove(label)
            
            # Save updated dataset metadata
            with open(os.path.join(self.active_dataset_path, 'metadata.json'), 'w') as f:
                json.dump(self.active_dataset, f, indent=2)
                
            logger.info(f"Removed recording from dataset: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing recording: {str(e)}")
            return False
    
    def extract_features(self, regenerate: bool = False) -> Dict:
        """
        Extract features from all recordings in the dataset.
        
        Args:
            regenerate: Whether to regenerate features for all recordings
            
        Returns:
            Dictionary of extracted features
        """
        if not self.active_dataset or not self.active_dataset_path:
            logger.error("No active dataset. Create or load one first.")
            return {}
            
        # Check if we already have features and don't need to regenerate
        if 'features' in self.active_dataset and not regenerate:
            logger.info("Using cached features. Set regenerate=True to recompute.")
            return self.active_dataset.get('features', {})
            
        recordings_dir = os.path.join(self.active_dataset_path, 'recordings')
        features = {'recordings': {}}
        
        # Aggregate statistics
        total_recordings = 0
        recording_durations = []
        recordings_by_label = {}
        
        # Process each recording
        for filename in os.listdir(recordings_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(recordings_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        recording = json.load(f)
                        
                    # Extract features
                    recording_features = self.analyzer.extract_features(recording)
                    
                    # Store features by filename
                    features['recordings'][filename] = recording_features
                    
                    # Update statistics
                    total_recordings += 1
                    
                    # Get duration
                    duration = recording.get('metadata', {}).get('duration_seconds', 0)
                    if duration > 0:
                        recording_durations.append(duration)
                    
                    # Update label stats
                    label = recording.get('metadata', {}).get('label')
                    if label:
                        if label not in recordings_by_label:
                            recordings_by_label[label] = []
                        recordings_by_label[label].append(filename)
                    
                except Exception as e:
                    logger.warning(f"Error extracting features for {filename}: {str(e)}")
        
        # Compute dataset-level statistics
        features['dataset_stats'] = {
            'recording_count': total_recordings,
            'avg_duration': np.mean(recording_durations) if recording_durations else 0,
            'min_duration': np.min(recording_durations) if recording_durations else 0,
            'max_duration': np.max(recording_durations) if recording_durations else 0,
            'total_duration': np.sum(recording_durations) if recording_durations else 0,
            'label_counts': {label: len(recs) for label, recs in recordings_by_label.items()},
            'label_distribution': {label: len(recs) / total_recordings for label, recs in recordings_by_label.items()} if total_recordings else {}
        }
        
        # Store features in dataset metadata
        self.active_dataset['features'] = features
        self.active_dataset['last_modified'] = datetime.now().isoformat()
        
        # Save updated dataset metadata
        with open(os.path.join(self.active_dataset_path, 'metadata.json'), 'w') as f:
            json.dump(self.active_dataset, f, indent=2)
            
        logger.info(f"Extracted features for {total_recordings} recordings")
        return features
    
    def export_features_csv(self, output_path: str = None) -> Optional[str]:
        """
        Export features from all recordings to a CSV file.
        
        Args:
            output_path: Path to save the CSV file (or None to use default location)
            
        Returns:
            Path to the saved CSV file, or None if export failed
        """
        if not self.active_dataset or not self.active_dataset_path:
            logger.error("No active dataset. Create or load one first.")
            return None
            
        # Extract features if needed
        features = self.extract_features()
        if not features:
            return None
            
        # Use default path if not specified
        if output_path is None:
            dataset_name = self.active_dataset.get('name', 'dataset').replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.active_dataset_path, f"{dataset_name}_features_{timestamp}.csv")
        
        try:
            # Prepare data for CSV export
            rows = []
            
            for filename, recording_features in features.get('recordings', {}).items():
                # Load the recording to get metadata
                filepath = os.path.join(self.active_dataset_path, 'recordings', filename)
                with open(filepath, 'r') as f:
                    recording = json.load(f)
                
                metadata = recording.get('metadata', {})
                
                # Create a row for this recording
                row = {
                    'filename': filename,
                    'label': metadata.get('label', ''),
                    'duration': metadata.get('duration_seconds', 0),
                    'frame_count': len(recording.get('frames', [])),
                    'timestamp': metadata.get('timestamp', '')
                }
                
                # Add trajectory features
                for landmark, distance in recording_features.get('total_distance', {}).items():
                    row[f'distance_{landmark}'] = distance
                
                # Add velocity features
                for landmark, velocity in recording_features.get('avg_velocity', {}).items():
                    row[f'velocity_{landmark}'] = velocity
                
                # Add smoothness features
                for landmark, smoothness in recording_features.get('smoothness', {}).items():
                    row[f'smoothness_{landmark}'] = smoothness
                
                # Add gesture count and frequency
                row['gesture_count'] = len(recording_features.get('gestures', []))
                row['gesture_frequency'] = recording_features.get('gesture_frequency', 0)
                
                # Add bounding box features
                bbox = recording_features.get('bounding_box', {})
                row['bbox_width'] = bbox.get('width', 0)
                row['bbox_height'] = bbox.get('height', 0)
                row['bbox_area'] = bbox.get('width', 0) * bbox.get('height', 0)
                
                rows.append(row)
            
            # Create DataFrame and export to CSV
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Exported features to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting features: {str(e)}")
            return None
