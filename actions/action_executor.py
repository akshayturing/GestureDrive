# actions/action_executor.py
from typing import Dict, Any, Callable, List, Optional
import logging
import importlib
import json
import os

class ActionExecutor:
    """
    Simplified action executor with cleaner mappings and conditionals.
    """
    
    def __init__(self, config_manager, event_bus):
        self.logger = logging.getLogger("ActionExecutor")
        self.config_manager = config_manager
        self.event_bus = event_bus
        
        # Current context
        self.current_context = "default"
        
        # Cache for action lookups
        self.action_cache = {}
        
        # Action handlers registered by modules
        self.action_handlers = {}
        
        # Load action mappings
        self.action_mappings = self._load_action_mappings()
        
        # Register for events
        event_bus.subscribe("gesture_detected", self.on_gesture_detected)
        event_bus.subscribe("motion_detected", self.on_motion_detected)
        event_bus.subscribe("context_changed", self.on_context_changed)
        
        # Load action handlers
        self._load_action_handlers()
    
    def _load_action_mappings(self) -> Dict:
        """
        Load action mappings from configuration.
        Simplified with cleaner structure.
        """
        mappings = self.config_manager.get("actions", {})
        
        if not mappings:
            # Default mappings if not configured
            mappings = {
                "default": {
                    "gestures": {
                        "point_up": "navigate.move_forward",
                        "point_down": "navigate.move_backward",
                        "point_left": "navigate.turn_left",
                        "point_right": "navigate.turn_right",
                        "open_palm": "navigate.stop",
                        "fist": "navigate.cancel"
                    },
                    "motions": {
                        "swipe_up": "scroll.up",
                        "swipe_down": "scroll.down",
                        "swipe_left": "navigate.back",
                        "swipe_right": "navigate.forward"
                    }
                },
                "file_browser": {
                    "gestures": {
                        "point_up": "files.select_previous",
                        "point_down": "files.select_next",
                        "open_palm": "files.refresh_directory",
                        "fist": "files.cancel_operation"
                    },
                    "motions": {
                        "swipe_up": "files.scroll_up",
                        "swipe_down": "files.scroll_down",
                        "swipe_left": "files.navigate_back",
                        "swipe_right": "files.enter_directory"
                    }
                }
            }
            
            # Save to config
            self.config_manager.set("actions", mappings)
            self.config_manager.save_config()
            
        return mappings
    
    def _load_action_handlers(self) -> None:
        """
        Load action handler modules dynamically.
        """
        # Look for action modules in the actions package
        action_modules = [
            'file_actions',
            'navigation_actions',
            'scroll_actions'  # Added for scroll actions
        ]
        
        for module_name in action_modules:
            try:
                module = importlib.import_module(f'gesture_drive.actions.{module_name}')
                
                # Register action handlers from module
                if hasattr(module, 'register_actions'):
                    handlers = module.register_actions(self.event_bus, self.config_manager)
                    if handlers:
                        self.action_handlers.update(handlers)
                        self.logger.info(f"Registered action handlers from {module_name}: {list(handlers.keys())}")
            except ImportError as e:
                self.logger.warning(f"Could not load action module {module_name}: {str(e)}")
    
    def set_context(self, context_name: str) -> bool:
        """
        Change the current context.
        Returns True if successful, False if context doesn't exist.
        """
        if context_name in self.action_mappings:
            # Only update and publish if context actually changed
            if self.current_context != context_name:
                old_context = self.current_context
                self.current_context = context_name
                
                # Clear action cache on context change
                self.action_cache.clear()
                
                # Notify about context change
                self.event_bus.publish("context_changed", {
                    "name": context_name,
                    "previous": old_context,
                    "timestamp": time.time()
                })
                
                self.logger.info(f"Context changed: {old_context} -> {context_name}")
            return True
        
        self.logger.warning(f"Invalid context: {context_name}")
        return False
    
    def on_gesture_detected(self, data: Dict) -> None:
        """
        Handle gesture detection events.
        Simplified with better error handling.
        """
        try:
            gesture = data.get('gesture')
            if not gesture:
                return
                
            # Get action with caching
            action_name = self._get_action(gesture, "gestures")
            if not action_name:
                return
            
            # Execute action
            self.execute_action(action_name, data)
            
        except Exception as e:
            self.logger.error(f"Error handling gesture: {str(e)}", exc_info=True)
    
    def on_motion_detected(self, data: Dict) -> None:
        """
        Handle motion detection events.
        Simplified with better error handling.
        """
        try:
            motion = data.get('motion')
            if not motion or motion == 'stationary' or motion == 'insufficient_data':
                return
                
            # Get action with caching
            action_name = self._get_action(motion, "motions")
            if not action_name:
                return
                
            # Execute action
            self.execute_action(action_name, data)
            
        except Exception as e:
            self.logger.error(f"Error handling motion: {str(e)}", exc_info=True)
    
    def on_context_changed(self, data: Dict) -> None:
        """
        Handle context change events from other components.
        """
        if 'name' in data and isinstance(data['name'], str):
            self.set_context(data['name'])
    
    def _get_action(self, trigger: str, mapping_type: str) -> Optional[str]:
        """
        Get the action for a trigger in the current context.
        Uses caching for performance.
        
        Args:
            trigger: Gesture or motion string
            mapping_type: Either "gestures" or "motions"
            
        Returns:
            Action name or None if not found
        """
        # Check cache first (context + type + trigger)
        cache_key = f"{self.current_context}:{mapping_type}:{trigger}"
        
        if cache_key in self.action_cache:
            return self.action_cache[cache_key]
            
        # Cache miss, look up the action
        action_name = None
        
        # Get mappings for current context
        context_mappings = self.action_mappings.get(self.current_context, {})
        
        # Get specific mapping type (gestures or motions)
        type_mappings = context_mappings.get(mapping_type, {})
        
        # Look up the trigger
        action_name = type_mappings.get(trigger)
        
        # Cache the result (including None)
        self.action_cache[cache_key] = action_name
        
        return action_name
    
    def execute_action(self, action_name: str, data: Dict) -> bool:
        """
        Execute an action by name.
        
        Args:
            action_name: The action to execute (format: "category.action")
            data: Data associated with the trigger
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not action_name or '.' not in action_name:
                self.logger.warning(f"Invalid action name: {action_name}")
                return False
                
            # Split into category and action
            category, action = action_name.split('.', 1)
            
            # Find the handler
            handler = self.action_handlers.get(category)
            
            if not handler:
                self.logger.warning(f"No handler for action category: {category}")
                return False
                
            # Check if the action exists
            if not hasattr(handler, action):
                self.logger.warning(f"Action '{action}' not found in handler '{category}'")
                return False
                
            # Call the method
            action_method = getattr(handler, action)
            action_method(data)
            
            self.logger.debug(f"Executed action: {action_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing action {action_name}: {str(e)}", exc_info=True)
            return False