# gesture_config_manager.py
import json
import os
import time
import logging
import importlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GestureConfigManager:
    """
    Manager class for loading, validating, and accessing gesture-action mappings
    from a JSON configuration file.
    """
    def __init__(self, config_path: str = "config/gesture_config.json"):
        self.config_path = config_path
        self.config = {}
        self.action_handlers = {}
        self.last_load_time = 0
        self.current_context = "default"
        # Store recent gestures for compound gesture detection
        self.recent_gestures = []
        self.max_gesture_history = 10
        
        # Load the configuration file
        self.load_config()
        
        # Initialize action handlers
        self.initialize_action_handlers()

    def load_config(self) -> bool:
        """
        Load the configuration file from disk.
        Returns True if successful, False otherwise.
        """
        try:
            # Check if the file exists
            if not os.path.exists(self.config_path):
                logger.error(f"Configuration file not found: {self.config_path}")
                return False
            
            # Check if the file has been modified since last load
            file_mtime = os.path.getmtime(self.config_path)
            if file_mtime <= self.last_load_time:
                # File hasn't been modified, no need to reload
                return True
            
            # Load and parse the JSON file
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Update the last load time
            self.last_load_time = file_mtime
            
            # Validate the configuration
            if not self._validate_config():
                logger.error("Invalid configuration file")
                return False
            
            logger.info(f"Successfully loaded gesture configuration from {self.config_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON configuration: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False

    def _validate_config(self) -> bool:
        """
        Validate the loaded configuration file.
        Returns True if valid, False otherwise.
        """
        required_keys = ["version", "individualGestures", "actions"]
        for key in required_keys:
            if key not in self.config:
                logger.error(f"Missing required key in configuration: {key}")
                return False
                
        # Validate that all referenced actions exist
        defined_actions = set(self.config["actions"].keys())
        
        # Check individual gestures
        for gesture_name, gesture_config in self.config.get("individualGestures", {}).items():
            action = gesture_config.get("action")
            if action and action not in defined_actions:
                logger.error(f"Gesture '{gesture_name}' references undefined action: {action}")
                return False
        
        # Check compound gestures
        for gesture_name, gesture_config in self.config.get("compoundGestures", {}).items():
            action = gesture_config.get("action")
            if action and action not in defined_actions:
                logger.error(f"Compound gesture '{gesture_name}' references undefined action: {action}")
                return False
                
            # Check that referenced individual gestures exist
            individual_gestures = set(self.config["individualGestures"].keys())
            if "sequence" in gesture_config:
                for g in gesture_config["sequence"]:
                    if g not in individual_gestures:
                        logger.error(f"Compound gesture '{gesture_name}' references undefined gesture: {g}")
                        return False
            
            if "concurrent" in gesture_config:
                for g in gesture_config["concurrent"]:
                    if g not in individual_gestures:
                        logger.error(f"Compound gesture '{gesture_name}' references undefined gesture: {g}")
                        return False
                
        return True

    def initialize_action_handlers(self):
        """
        Initialize action handlers by dynamically importing the modules and getting
        references to the handler functions.
        """
        for action_name, action_config in self.config.get("actions", {}).items():
            handler_path = action_config.get("handler", "")
            
            if not handler_path:
                logger.warning(f"No handler specified for action: {action_name}")
                continue
                
            try:
                # Parse the handler path (module.function or module.class.method)
                parts = handler_path.split('.')
                
                if len(parts) < 2:
                    logger.error(f"Invalid handler format for {action_name}: {handler_path}")
                    continue
                    
                module_path = '.'.join(parts[:-1])
                function_name = parts[-1]
                
                # Import the module
                module = importlib.import_module(module_path)
                
                # Get the handler function
                handler = getattr(module, function_name)
                self.action_handlers[action_name] = handler
                
                logger.info(f"Initialized handler for action: {action_name}")
                
            except ImportError as e:
                logger.error(f"Could not import module for action {action_name}: {e}")
            except AttributeError as e:
                logger.error(f"Could not find handler for action {action_name}: {e}")
            except Exception as e:
                logger.error(f"Error initializing handler for action {action_name}: {e}")

    def get_action_for_gesture(self, gesture_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the action configuration for a given gesture name, considering the current context.
        Returns None if the gesture is not defined or disabled.
        """
        # Check if we need to reload the configuration (for hot reloading)
        self.check_reload_config()
        
        # First, check contextual mappings
        context_mappings = self.config.get("contextualMappings", {}).get(self.current_context, {})
        context_gesture_mappings = context_mappings.get("gestureMappings", {})
        
        if gesture_name in context_gesture_mappings:
            gesture_config = context_gesture_mappings[gesture_name]
            if gesture_config.get("enabled", True):
                action_name = gesture_config.get("action")
                if action_name:
                    return {
                        "action": action_name,
                        "params": gesture_config.get("params", {}),
                        "description": gesture_config.get("description", "")
                    }
        
        # If not in contextual mappings, check individual gestures
        if gesture_name in self.config.get("individualGestures", {}):
            gesture_config = self.config["individualGestures"][gesture_name]
            if gesture_config.get("enabled", True):
                action_name = gesture_config.get("action")
                if action_name:
                    return {
                        "action": action_name,
                        "params": gesture_config.get("params", {}),
                        "description": gesture_config.get("description", "")
                    }
        
        return None

    def process_gesture(self, gesture_name: str, timestamp: float = None) -> Optional[Dict[str, Any]]:
        """
        Process a detected gesture, handling both individual gestures and compound gestures.
        Returns the action details if a gesture (individual or compound) is recognized.
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Record this gesture in our history for compound gesture detection
        self.record_gesture(gesture_name, timestamp)
        
        # Check for compound gestures first
        compound_action = self.check_compound_gestures()
        if compound_action:
            return compound_action
            
        # If no compound gesture matched, process as individual gesture
        return self.get_action_for_gesture(gesture_name)

    def record_gesture(self, gesture_name: str, timestamp: float):
        """
        Record a gesture in the history for compound gesture detection.
        """
        self.recent_gestures.append({
            "name": gesture_name,
            "timestamp": timestamp
        })
        
        # Trim history if it gets too long
        if len(self.recent_gestures) > self.max_gesture_history:
            self.recent_gestures = self.recent_gestures[-self.max_gesture_history:]

    def check_compound_gestures(self) -> Optional[Dict[str, Any]]:
        """
        Check if the recent gesture history matches any defined compound gestures.
        Returns the action details if a compound gesture is recognized.
        """
        if not self.recent_gestures:
            return None
            
        # Sort compound gestures by priority (higher priority first)
        compound_gestures = sorted(
            self.config.get("compoundGestures", {}).items(),
            key=lambda x: x[1].get("priority", 0),
            reverse=True
        )
        
        for gesture_name, gesture_config in compound_gestures:
            if not gesture_config.get("enabled", True):
                continue
                
            # Check sequential gestures
            if "sequence" in gesture_config:
                sequence = gesture_config["sequence"]
                max_time_between = gesture_config.get("maxTimeBetweenMs", 1500) / 1000.0  # Convert to seconds
                
                if self.check_sequence_match(sequence, max_time_between):
                    action_name = gesture_config.get("action")
                    if action_name:
                        # Clear the history to prevent double-triggering
                        self.recent_gestures = []
                        return {
                            "action": action_name,
                            "params": gesture_config.get("params", {}),
                            "description": gesture_config.get("description", ""),
                            "compound": True,
                            "gesture_name": gesture_name
                        }
            
            # Check concurrent gestures
            if "concurrent" in gesture_config:
                concurrent_gestures = gesture_config["concurrent"]
                concurrent_window = gesture_config.get("concurrentWindowMs", 500) / 1000.0  # Convert to seconds
                
                if self.check_concurrent_match(concurrent_gestures, concurrent_window):
                    action_name = gesture_config.get("action")
                    if action_name:
                        # Clear the history to prevent double-triggering
                        self.recent_gestures = []
                        return {
                            "action": action_name,
                            "params": gesture_config.get("params", {}),
                            "description": gesture_config.get("description", ""),
                            "compound": True,
                            "gesture_name": gesture_name
                        }
        
        return None

    def check_sequence_match(self, sequence: List[str], max_time_between: float) -> bool:
        """
        Check if the recent gesture history contains the specified sequence in order.
        """
        if len(sequence) > len(self.recent_gestures):
            return False
            
        # Get the most recent gestures that could match the sequence
        recent = self.recent_gestures[-len(sequence):]
        
        # Check if the sequence matches
        for i, gesture in enumerate(sequence):
            if recent[i]["name"] != gesture:
                return False
                
            # Check time constraints for sequential gestures
            if i > 0:
                time_diff = recent[i]["timestamp"] - recent[i-1]["timestamp"]
                if time_diff > max_time_between:
                    return False
        
        return True

    def check_concurrent_match(self, concurrent_gestures: List[str], time_window: float) -> bool:
        """
        Check if all the specified gestures occurred within the time window.
        """
        if len(concurrent_gestures) == 0:
            return False
            
        # Get the timestamps of the most recent occurrences of each gesture
        latest_times = {}
        for gesture in self.recent_gestures:
            name = gesture["name"]
            if name in concurrent_gestures:
                latest_times[name] = gesture["timestamp"]
        
        # Check if we found all required gestures
        if len(latest_times) != len(concurrent_gestures):
            return False
            
        # Check if all gestures occurred within the time window
        timestamps = list(latest_times.values())
        time_diff = max(timestamps) - min(timestamps)
        return time_diff <= time_window

    def execute_action(self, action_details: Dict[str, Any], context_data: Dict[str, Any] = None) -> Any:
        """
        Execute the action specified in action_details with the given parameters.
        """
        if not action_details:
            return None
            
        action_name = action_details.get("action")
        params = action_details.get("params", {})
        
        if not action_name:
            logger.error("No action name specified in action details")
            return None
            
        # Check if we have a handler for this action
        if action_name not in self.action_handlers:
            logger.error(f"No handler registered for action: {action_name}")
            return None
            
        handler = self.action_handlers[action_name]
        
        try:
            # Execute the handler with parameters
            if context_data:
                # Add context data to params
                combined_params = {**params, **context_data}
                return handler(**combined_params)
            else:
                return handler(**params)
                
        except Exception as e:
            logger.error(f"Error executing action {action_name}: {e}")
            return None

    def set_context(self, context: str):
        """
        Set the current application context for contextual gesture mappings.
        """
        if context != self.current_context:
            self.current_context = context
            logger.info(f"Gesture context set to: {context}")

    def check_reload_config(self):
        """
        Check if the configuration file has been modified and reload if necessary.
        """
        if os.path.exists(self.config_path):
            file_mtime = os.path.getmtime(self.config_path)
            if file_mtime > self.last_load_time:
                logger.info("Configuration file modified, reloading...")
                self.load_config()
                self.initialize_action_handlers()

    def get_available_gestures(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a dictionary of all available gestures and their descriptions.
        """
        result = {}
        
        # Individual gestures
        for name, config in self.config.get("individualGestures", {}).items():
            if config.get("enabled", True):
                result[name] = {
                    "description": config.get("description", ""),
                    "action": config.get("action", ""),
                    "type": "individual"
                }
        
        # Compound gestures
        for name, config in self.config.get("compoundGestures", {}).items():
            if config.get("enabled", True):
                result[name] = {
                    "description": config.get("description", ""),
                    "action": config.get("action", ""),
                    "type": "compound"
                }
                
        return result
        
    def get_gesture_configuration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current gesture configuration for display in the UI.
        """
        return {
            "version": self.config.get("version", "unknown"),
            "lastModified": self.config.get("lastModified", datetime.now().isoformat()),
            "currentContext": self.current_context,
            "availableContexts": list(self.config.get("contextualMappings", {}).keys()),
            "individualGestureCount": len(self.config.get("individualGestures", {})),
            "compoundGestureCount": len(self.config.get("compoundGestures", {})),
            "actionCount": len(self.config.get("actions", {})),
            "availableGestures": self.get_available_gestures()
        }
