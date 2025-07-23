# profile_manager.py
import os
import json
import shutil
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfileManager:
    """
    Manages gesture profiles, including loading, saving, validation, and switching between profiles.
    Supports user-specific profile collections and validation to prevent unsafe configurations.
    """
    
    PROFILE_DIR = "profiles"
    USER_PROFILE_DIR = os.path.join(PROFILE_DIR, "user_profiles")
    DEFAULT_PROFILE = os.path.join(PROFILE_DIR, "default.json")
    SYSTEM_ACTIONS = [
        "navigateBack", "enterDirectory", "refreshDirectory", "cancelOperation",
        "scroll", "moveSelection", "showContextMenu", "zoom"
    ]
    RESTRICTED_ACTIONS = ["deleteFile", "renameFile", "moveFile", "compressFile"]
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,16}$')
    
    def __init__(self, active_profile: str = "default", username: str = None):
        """
        Initialize the profile manager.
        
        Args:
            active_profile: Name of the profile to load initially
            username: Current username (if applicable)
        """
        self.active_profile = active_profile
        self.username = username
        self.current_config = {}
        self.available_profiles = []
        self.gesture_config_manager = None  # Will be set later
        
        # Ensure profile directories exist
        self._ensure_profile_directories()
        
        # Load the list of available profiles
        self.refresh_available_profiles()
        
        # Load the active profile
        self.load_profile(active_profile)
    
    def set_gesture_config_manager(self, gesture_config_manager):
        """Set the gesture config manager reference for applying profiles"""
        self.gesture_config_manager = gesture_config_manager
        
    def _ensure_profile_directories(self):
        """Ensure all necessary profile directories exist"""
        os.makedirs(self.PROFILE_DIR, exist_ok=True)
        os.makedirs(self.USER_PROFILE_DIR, exist_ok=True)
        
        # Create default profile if it doesn't exist
        if not os.path.exists(self.DEFAULT_PROFILE):
            self._create_default_profile()
    
    def _create_default_profile(self):
        """Create a default profile with basic gesture mappings"""
        from core.gesture_config_manager import GestureConfigManager
        
        # Get configuration from the gesture config manager's default
        temp_manager = GestureConfigManager()
        default_config = temp_manager.config
        
        # Add profile metadata
        default_config.update({
            "profileName": "Default",
            "description": "Default gesture profile with basic file navigation and management",
            "created": datetime.now().isoformat(),
            "lastModified": datetime.now().isoformat(),
            "author": "System"
        })
        
        # Save the default profile
        with open(self.DEFAULT_PROFILE, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    def refresh_available_profiles(self):
        """Refresh the list of available profiles"""
        self.available_profiles = []
        
        # Add default profile
        if os.path.exists(self.DEFAULT_PROFILE):
            self.available_profiles.append({
                "id": "default",
                "name": "Default",
                "type": "system",
                "path": self.DEFAULT_PROFILE
            })
        
        # Add user profiles (shared)
        for filename in os.listdir(self.USER_PROFILE_DIR):
            if filename.endswith('.json'):
                profile_id = filename[:-5]  # Remove .json
                profile_path = os.path.join(self.USER_PROFILE_DIR, filename)
                
                try:
                    with open(profile_path, 'r') as f:
                        profile_data = json.load(f)
                    
                    self.available_profiles.append({
                        "id": profile_id,
                        "name": profile_data.get("profileName", profile_id),
                        "description": profile_data.get("description", ""),
                        "author": profile_data.get("author", "Unknown"),
                        "created": profile_data.get("created"),
                        "lastModified": profile_data.get("lastModified"),
                        "type": "shared",
                        "path": profile_path
                    })
                except Exception as e:
                    logger.error(f"Error loading profile {profile_id}: {e}")
        
        # Add user-specific profiles if a username is provided
        if self.username:
            user_profile_dir = os.path.join(self.USER_PROFILE_DIR, self.username)
            if os.path.exists(user_profile_dir):
                for filename in os.listdir(user_profile_dir):
                    if filename.endswith('.json'):
                        profile_id = f"{self.username}/{filename[:-5]}"
                        profile_path = os.path.join(user_profile_dir, filename)
                        
                        try:
                            with open(profile_path, 'r') as f:
                                profile_data = json.load(f)
                            
                            self.available_profiles.append({
                                "id": profile_id,
                                "name": profile_data.get("profileName", profile_id),
                                "description": profile_data.get("description", ""),
                                "author": profile_data.get("author", self.username),
                                "created": profile_data.get("created"),
                                "lastModified": profile_data.get("lastModified"),
                                "type": "user",
                                "path": profile_path
                            })
                        except Exception as e:
                            logger.error(f"Error loading profile {profile_id}: {e}")
    
    def load_profile(self, profile_id: str) -> bool:
        """
        Load a gesture profile by ID.
        
        Args:
            profile_id: The ID of the profile to load
            
        Returns:
            bool: True if the profile was loaded successfully, False otherwise
        """
        # Find the profile in available profiles
        profile = next((p for p in self.available_profiles if p["id"] == profile_id), None)
        
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return False
        
        try:
            with open(profile["path"], 'r') as f:
                self.current_config = json.load(f)
                
            # Set the active profile
            self.active_profile = profile_id
            
            # Apply the configuration to the gesture config manager if available
            if self.gesture_config_manager:
                # Create a copy without the profile metadata
                config_copy = self.current_config.copy()
                for key in ["profileName", "description", "created", "lastModified", "author"]:
                    if key in config_copy:
                        del config_copy[key]
                
                # Set the configuration
                self.gesture_config_manager.config = config_copy
                self.gesture_config_manager.initialize_action_handlers()
                
            logger.info(f"Successfully loaded profile: {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading profile {profile_id}: {e}")
            return False
    
    def save_profile(self, profile_data: dict, profile_id: str = None, overwrite: bool = False) -> Optional[str]:
        """
        Save a profile to disk.
        
        Args:
            profile_data: The profile data to save
            profile_id: The ID to use for the profile (if None, generate one)
            overwrite: Whether to overwrite an existing profile
            
        Returns:
            str: The ID of the saved profile, or None if saving failed
        """
        # Validate the profile data
        validation_result = self.validate_profile(profile_data)
        if not validation_result["valid"]:
            logger.error(f"Invalid profile data: {validation_result['errors']}")
            return None
        
        # Generate a profile ID if not provided
        if not profile_id:
            profile_name = profile_data.get("profileName", "Untitled")
            profile_id = self._generate_profile_id(profile_name)
        
        # Determine the profile path
        is_user_profile = False
        if '/' in profile_id and profile_id.split('/')[0] == self.username:
            # User-specific profile
            user, name = profile_id.split('/')
            profile_dir = os.path.join(self.USER_PROFILE_DIR, user)
            os.makedirs(profile_dir, exist_ok=True)
            profile_path = os.path.join(profile_dir, f"{name}.json")
            is_user_profile = True
        else:
            # Shared profile
            profile_path = os.path.join(self.USER_PROFILE_DIR, f"{profile_id}.json")
        
        # Check if the profile already exists
        if os.path.exists(profile_path) and not overwrite:
            logger.error(f"Profile already exists: {profile_id}")
            return None
        
        # Add metadata if not present
        if "created" not in profile_data:
            profile_data["created"] = datetime.now().isoformat()
        
        profile_data["lastModified"] = datetime.now().isoformat()
        
        if "author" not in profile_data:
            profile_data["author"] = self.username or "Unknown"
        
        try:
            # Write the profile to disk
            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            logger.info(f"Successfully saved profile: {profile_id}")
            
            # Refresh the list of available profiles
            self.refresh_available_profiles()
            
            return profile_id
            
        except Exception as e:
            logger.error(f"Error saving profile {profile_id}: {e}")
            return None
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a profile.
        
        Args:
            profile_id: The ID of the profile to delete
            
        Returns:
            bool: True if the profile was deleted, False otherwise
        """
        if profile_id == "default":
            logger.error("Cannot delete the default profile")
            return False
        
        # Find the profile in available profiles
        profile = next((p for p in self.available_profiles if p["id"] == profile_id), None)
        
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return False
        
        # Check if the user has permission to delete this profile
        if profile["type"] == "user" and not profile_id.startswith(f"{self.username}/"):
            logger.error(f"Permission denied: Cannot delete another user's profile")
            return False
        
        try:
            # Delete the profile file
            os.remove(profile["path"])
            
            logger.info(f"Successfully deleted profile: {profile_id}")
            
            # If this was the active profile, switch to default
            if profile_id == self.active_profile:
                self.load_profile("default")
            
            # Refresh the list of available profiles
            self.refresh_available_profiles()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting profile {profile_id}: {e}")
            return False
    
    def rename_profile(self, profile_id: str, new_name: str) -> Optional[str]:
        """
        Rename a profile.
        
        Args:
            profile_id: The ID of the profile to rename
            new_name: The new profile name
            
        Returns:
            str: The new profile ID, or None if renaming failed
        """
        if profile_id == "default":
            logger.error("Cannot rename the default profile")
            return None
        
        # Find the profile in available profiles
        profile = next((p for p in self.available_profiles if p["id"] == profile_id), None)
        
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return None
        
        # Check if the user has permission to rename this profile
        if profile["type"] == "user" and not profile_id.startswith(f"{self.username}/"):
            logger.error(f"Permission denied: Cannot rename another user's profile")
            return None
        
        try:
            # Load the profile data
            with open(profile["path"], 'r') as f:
                profile_data = json.load(f)
            
            # Update the profile name
            profile_data["profileName"] = new_name
            
            # Generate a new ID based on the new name
            if profile["type"] == "user":
                user, _ = profile_id.split('/')
                new_id = f"{user}/{self._sanitize_id(new_name)}"
            else:
                new_id = self._sanitize_id(new_name)
            
            # Save the profile with the new ID
            result = self.save_profile(profile_data, new_id)
            
            if result:
                # Delete the old profile file
                os.remove(profile["path"])
                
                # If this was the active profile, switch to the new one
                if profile_id == self.active_profile:
                    self.load_profile(new_id)
                
                # Refresh the list of available profiles
                self.refresh_available_profiles()
            
            return result
            
        except Exception as e:
            logger.error(f"Error renaming profile {profile_id}: {e}")
            return None
    
    def clone_profile(self, profile_id: str, new_name: str, as_user_profile: bool = False) -> Optional[str]:
        """
        Clone a profile.
        
        Args:
            profile_id: The ID of the profile to clone
            new_name: The name for the cloned profile
            as_user_profile: Whether to create as a user-specific profile
            
        Returns:
            str: The new profile ID, or None if cloning failed
        """
        # Find the profile in available profiles
        profile = next((p for p in self.available_profiles if p["id"] == profile_id), None)
        
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return None
        
        try:
            # Load the profile data
            with open(profile["path"], 'r') as f:
                profile_data = json.load(f)
            
            # Update metadata
            profile_data["profileName"] = new_name
            profile_data["description"] = f"Clone of {profile['name']}"
            profile_data["created"] = datetime.now().isoformat()
            profile_data["lastModified"] = datetime.now().isoformat()
            profile_data["author"] = self.username or "Unknown"
            
            # Generate new ID
            if as_user_profile and self.username:
                new_id = f"{self.username}/{self._sanitize_id(new_name)}"
            else:
                new_id = self._sanitize_id(new_name)
            
            # Save the cloned profile
            return self.save_profile(profile_data, new_id)
            
        except Exception as e:
            logger.error(f"Error cloning profile {profile_id}: {e}")
            return None
    
    def validate_profile(self, profile_data: dict) -> dict:
        """
        Validate a profile configuration for safety and correctness.
        
        Args:
            profile_data: The profile data to validate
            
        Returns:
            dict: Validation result with 'valid' boolean and list of 'errors'
        """
        errors = []
        
        # Check for required profile fields
        required_fields = ["profileName", "version", "individualGestures", "actions"]
        for field in required_fields:
            if field not in profile_data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return {"valid": False, "errors": errors}
        
        # Validate profile name
        if not isinstance(profile_data.get("profileName"), str):
            errors.append("Profile name must be a string")
        elif len(profile_data.get("profileName", "")) < 3:
            errors.append("Profile name must be at least 3 characters")
        
        # Validate gesture mappings
        individual_gestures = profile_data.get("individualGestures", {})
        compound_gestures = profile_data.get("compoundGestures", {})
        defined_actions = profile_data.get("actions", {})
        
        # Check for valid actions in individual gestures
        for gesture_name, gesture_config in individual_gestures.items():
            action = gesture_config.get("action")
            if action and action not in defined_actions:
                errors.append(f"Gesture '{gesture_name}' references undefined action: {action}")
        
        # Check for valid actions in compound gestures
        for gesture_name, gesture_config in compound_gestures.items():
            action = gesture_config.get("action")
            if action and action not in defined_actions:
                errors.append(f"Compound gesture '{gesture_name}' references undefined action: {action}")
                
            # Check that reference gestures exist
            if "sequence" in gesture_config:
                for g in gesture_config["sequence"]:
                    if g not in individual_gestures:
                        errors.append(f"Compound gesture '{gesture_name}' references undefined gesture: {g}")
            
            if "concurrent" in gesture_config:
                for g in gesture_config["concurrent"]:
                    if g not in individual_gestures:
                        errors.append(f"Compound gesture '{gesture_name}' references undefined gesture: {g}")
        
        # Check for potentially unsafe operations
        for action_name, action_config in defined_actions.items():
            handler = action_config.get("handler", "")
            
            # Check if the action involves potentially dangerous operations
            if action_name in self.RESTRICTED_ACTIONS:
                # Require confirmation for dangerous operations
                if not action_config.get("requiresConfirmation", False):
                    errors.append(f"Potentially dangerous action '{action_name}' must require confirmation")
        
        # Check for overlapping gestures
        gestures_seen = {}
        for gesture_name, gesture_config in individual_gestures.items():
            if gesture_config.get("enabled", True):
                # Check for gestures with the same base name but different modifiers
                base_gesture = gesture_name.split('_')[0]
                if base_gesture in gestures_seen:
                    # This is OK as long as they have different modifiers
                    pass
                gestures_seen[base_gesture] = gesture_name
        
        # Return validation results
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _sanitize_id(self, name: str) -> str:
        """Convert a profile name to a safe ID"""
        # Replace spaces with underscores and remove special characters
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', name.replace(' ', '_').lower())
        # Ensure ID is not empty
        return safe_id or "unnamed_profile"
    
    def _generate_profile_id(self, name: str) -> str:
        """Generate a profile ID based on the profile name"""
        base_id = self._sanitize_id(name)
        
        # Check if the ID already exists
        existing_ids = [p["id"] for p in self.available_profiles]
        
        if base_id not in existing_ids:
            return base_id
        
        # If ID exists, add a number suffix
        counter = 1
        while f"{base_id}_{counter}" in existing_ids:
            counter += 1
        
        return f"{base_id}_{counter}"
    
    def get_profile_info(self, profile_id: str = None) -> Optional[dict]:
        """
        Get information about a profile.
        
        Args:
            profile_id: The ID of the profile (or the active profile if None)
            
        Returns:
            dict: Profile information or None if not found
        """
        if profile_id is None:
            profile_id = self.active_profile
            
        return next((p for p in self.available_profiles if p["id"] == profile_id), None)
    
    def create_new_profile(self, name: str, description: str, as_user_profile: bool = False) -> Optional[str]:
        """
        Create a new empty profile.
        
        Args:
            name: The name for the new profile
            description: A description for the profile
            as_user_profile: Whether to create as a user-specific profile
            
        Returns:
            str: The new profile ID, or None if creation failed
        """
        # Start with a copy of the default profile
        try:
            with open(self.DEFAULT_PROFILE, 'r') as f:
                profile_data = json.load(f)
                
            # Update metadata
            profile_data["profileName"] = name
            profile_data["description"] = description
            profile_data["created"] = datetime.now().isoformat()
            profile_data["lastModified"] = datetime.now().isoformat()
            profile_data["author"] = self.username or "Unknown"
            
            # Generate new ID
            if as_user_profile and self.username:
                profile_id = f"{self.username}/{self._sanitize_id(name)}"
            else:
                profile_id = self._sanitize_id(name)
                
            # Save the new profile
            return self.save_profile(profile_data, profile_id)
            
        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            return None
            
    def export_profile(self, profile_id: str, export_path: str) -> bool:
        """
        Export a profile to a file.
        
        Args:
            profile_id: The ID of the profile to export
            export_path: The path to export to
            
        Returns:
            bool: True if the profile was exported successfully, False otherwise
        """
        # Find the profile in available profiles
        profile = next((p for p in self.available_profiles if p["id"] == profile_id), None)
        
        if not profile:
            logger.error(f"Profile not found: {profile_id}")
            return False
            
        try:
            # Copy the profile file to the export path
            shutil.copy2(profile["path"], export_path)
            
            logger.info(f"Successfully exported profile {profile_id} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting profile {profile_id}: {e}")
            return False
    
    def import_profile(self, import_path: str, new_name: str = None, as_user_profile: bool = False) -> Optional[str]:
        """
        Import a profile from a file.
        
        Args:
            import_path: The path of the profile file to import
            new_name: Optional new name for the imported profile
            as_user_profile: Whether to import as a user-specific profile
            
        Returns:
            str: The ID of the imported profile, or None if importing failed
        """
        try:
            # Load the profile data
            with open(import_path, 'r') as f:
                profile_data = json.load(f)
                
            # Validate the profile
            validation_result = self.validate_profile(profile_data)
            if not validation_result["valid"]:
                logger.error(f"Invalid profile data: {validation_result['errors']}")
                return None
                
            # Update metadata if a new name is provided
            if new_name:
                profile_data["profileName"] = new_name
                
            profile_data["lastModified"] = datetime.now().isoformat()
            profile_data["author"] = self.username or "Unknown"
                
            # Generate profile ID
            if as_user_profile and self.username:
                profile_id = f"{self.username}/{self._sanitize_id(profile_data['profileName'])}"
            else:
                profile_id = self._sanitize_id(profile_data['profileName'])
                
            # Save the imported profile
            return self.save_profile(profile_data, profile_id)
            
        except Exception as e:
            logger.error(f"Error importing profile: {e}")
            return None