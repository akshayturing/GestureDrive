# directory_state_manager.py

import os
import json
import time
import shutil
import threading
import pathlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DirectoryStateManager')

class DirectoryStateManager:
    """
    Manages persistent directory state across gesture interactions and application sessions.
    Provides thread-safe access to directory state, history, and favorites.
    Ensures real-time synchronization of directory changes.
    """
    
    # Default state file location in user's home directory
    DEFAULT_STATE_FILE = os.path.join(os.path.expanduser("~"), ".gesture_drive_state.json")
    
    def __init__(self, state_file: str = None, auto_save: bool = True, 
                 max_history: int = 100, save_interval: float = 5.0):
        """
        Initialize the directory state manager.
        
        Args:
            state_file: Path to the state file (default: ~/.gesture_drive_state.json)
            auto_save: Whether to automatically save state changes
            max_history: Maximum number of directories to keep in history
            save_interval: How often to auto-save in seconds (if auto_save is True)
        """
        # State file location
        self.state_file = state_file if state_file else self.DEFAULT_STATE_FILE
        
        # State settings
        self.auto_save = auto_save
        self.max_history = max_history
        self.save_interval = save_interval
        self.last_save_time = 0
        
        # Lock for thread safety
        self.state_lock = threading.RLock()
        
        # Transaction management
        self.transaction_id = 0
        self.transaction_log = []
        self.max_log_entries = 1000
        
        # Directory state
        self.state = {
            'current_directory': str(Path.cwd()),
            'history': [],  # List of visited directories
            'history_position': 0,
            'favorites': {},  # Named directory shortcuts
            'last_selected_indices': {},  # Remember selection per directory
            'metadata': {
                'version': '1.0',
                'last_updated': time.time(),
                'last_session': time.time(),
            }
        }
        
        # Load initial state
        self._load_state()
        
        # Validate current directory
        self._validate_current_directory()
        
        # Background auto-save thread
        self._shutdown_flag = threading.Event()
        if auto_save:
            self._auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
            self._auto_save_thread.start()
        else:
            self._auto_save_thread = None
            
    def _validate_current_directory(self):
        """Ensure the current directory exists and is accessible."""
        with self.state_lock:
            current_dir = Path(self.state['current_directory'])
            
            # If directory doesn't exist or isn't accessible, reset to home directory
            if not current_dir.exists() or not current_dir.is_dir():
                logger.warning(f"Current directory {current_dir} no longer exists. Resetting to home.")
                self.state['current_directory'] = str(Path.home())
                
            # Ensure working directory matches our state
            try:
                os.chdir(self.state['current_directory'])
            except (PermissionError, OSError) as e:
                logger.warning(f"Could not change to {self.state['current_directory']}: {e}")
                self.state['current_directory'] = str(Path.home())
                os.chdir(self.state['current_directory'])
    
    def _load_state(self):
        """Load directory state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    loaded_state = json.load(f)
                    
                # Validate and merge the loaded state
                with self.state_lock:
                    # Update all fields that exist in loaded state
                    for key in self.state.keys():
                        if key in loaded_state:
                            self.state[key] = loaded_state[key]
                    
                    # Update session metadata
                    self.state['metadata']['last_session'] = time.time()
                    
                logger.info(f"Loaded directory state from {self.state_file}")
            else:
                logger.info(f"State file {self.state_file} not found. Using default state.")
                self._save_state()  # Create initial state file
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading state file: {e}")
            
            # Backup corrupted state file
            if os.path.exists(self.state_file):
                backup_file = f"{self.state_file}.bak.{int(time.time())}"
                try:
                    shutil.copy2(self.state_file, backup_file)
                    logger.info(f"Created backup of corrupted state file: {backup_file}")
                except IOError as be:
                    logger.error(f"Failed to backup corrupted state file: {be}")
            
            # Reset to default state
            self._save_state()
    
    def _save_state(self):
        """Save current directory state to file."""
        try:
            # Update timestamp
            with self.state_lock:
                self.state['metadata']['last_updated'] = time.time()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(self.state_file)), exist_ok=True)
                
                # Write state file
                with open(self.state_file, 'w') as f:
                    json.dump(self.state, f, indent=2)
                    
                self.last_save_time = time.time()
                logger.debug(f"Saved directory state to {self.state_file}")
                
        except IOError as e:
            logger.error(f"Error saving state file: {e}")
    
    def _auto_save_worker(self):
        """Background thread for periodic state saving."""
        while not self._shutdown_flag.is_set():
            current_time = time.time()
            
            # Check if we need to save based on time interval
            if current_time - self.last_save_time >= self.save_interval:
                self._save_state()
                
            # Sleep to reduce CPU usage (check shutdown flag every 0.5 seconds)
            for _ in range(int(self.save_interval * 2)):
                if self._shutdown_flag.is_set():
                    break
                time.sleep(0.5)
    
    def get_current_directory(self) -> Path:
        """Get the current working directory."""
        with self.state_lock:
            return Path(self.state['current_directory'])
    
    def change_directory(self, path: str or Path) -> bool:
        """
        Change the current working directory and update state.
        
        Args:
            path: Target directory path
            
        Returns:
            Success status
        """
        target_path = Path(path) if isinstance(path, str) else path
        
        # Start a transaction for this operation
        transaction_id = self._begin_transaction("change_directory")
        
        try:
            # Verify the path exists and is a directory
            if not target_path.exists() or not target_path.is_dir():
                self._end_transaction(transaction_id, False)
                return False
                
            # Update directory state
            with self.state_lock:
                # Save current index
                self._save_selection_index(self.state['current_directory'])
                
                # Change directory and update state
                old_dir = self.state['current_directory']
                self.state['current_directory'] = str(target_path.resolve())
                
                # Update actual working directory
                os.chdir(self.state['current_directory'])
                
                # Update history if path is different
                if old_dir != self.state['current_directory']:
                    # Truncate forward history if navigating from middle
                    if self.state['history_position'] < len(self.state['history']) - 1:
                        self.state['history'] = self.state['history'][:self.state['history_position'] + 1]
                        
                    # Add to history
                    self.state['history'].append(self.state['current_directory'])
                    
                    # Limit history size
                    if len(self.state['history']) > self.max_history:
                        self.state['history'] = self.state['history'][-self.max_history:]
                        
                    self.state['history_position'] = len(self.state['history']) - 1
                    
                # If auto-save is disabled, save explicitly on directory changes
                if not self.auto_save:
                    self._save_state()
                    
                self._end_transaction(transaction_id, True)
                return True
                
        except (PermissionError, OSError) as e:
            logger.error(f"Error changing directory to {target_path}: {e}")
            self._end_transaction(transaction_id, False, str(e))
            return False
    
    def navigate_history(self, forward: bool = True) -> bool:
        """
        Navigate forward or backward in the directory history.
        
        Args:
            forward: True to go forward, False to go backward
            
        Returns:
            Success status
        """
        transaction_id = self._begin_transaction("navigate_history", {"direction": "forward" if forward else "backward"})
        
        try:
            with self.state_lock:
                # Save current index
                self._save_selection_index(self.state['current_directory'])
                
                # Determine new position
                new_position = self.state['history_position'] + (1 if forward else -1)
                
                # Check if the new position is valid
                if new_position < 0 or new_position >= len(self.state['history']):
                    self._end_transaction(transaction_id, False, "End of history reached")
                    return False
                
                # Update position
                self.state['history_position'] = new_position
                
                # Get target directory
                target_dir = self.state['history'][new_position]
                
                # Verify directory still exists
                if not Path(target_dir).exists() or not Path(target_dir).is_dir():
                    logger.warning(f"History directory {target_dir} no longer exists.")
                    # Remove invalid entry and retry
                    del self.state['history'][new_position]
                    if new_position >= len(self.state['history']):
                        new_position = max(0, len(self.state['history']) - 1)
                    self.state['history_position'] = new_position
                    
                    if len(self.state['history']) == 0:
                        # If history is empty, add current directory
                        self.state['history'] = [str(Path.cwd())]
                        self.state['history_position'] = 0
                        self._end_transaction(transaction_id, False, "History invalid, reset to current directory")
                        return False
                    
                    # Now use the valid directory
                    target_dir = self.state['history'][new_position]
                
                # Update current directory
                self.state['current_directory'] = target_dir
                
                # Update actual working directory
                os.chdir(self.state['current_directory'])
                
                # If auto-save is disabled, save explicitly on navigation
                if not self.auto_save:
                    self._save_state()
                    
                self._end_transaction(transaction_id, True)
                return True
                
        except (PermissionError, OSError) as e:
            logger.error(f"Error navigating history: {e}")
            self._end_transaction(transaction_id, False, str(e))
            return False
    
    def navigate_up(self) -> bool:
        """Navigate to the parent directory."""
        current_dir = self.get_current_directory()
        parent_dir = current_dir.parent
        
        # Check if already at root
        if parent_dir == current_dir:
            return False
            
        return self.change_directory(parent_dir)
    
    def get_selection_index(self, directory: str = None) -> int:
        """
        Get the last selection index for a directory.
        
        Args:
            directory: Directory path (defaults to current directory)
            
        Returns:
            The saved index or 0 if not found
        """
        with self.state_lock:
            dir_path = directory or self.state['current_directory']
            return self.state['last_selected_indices'].get(dir_path, 0)
    
    def _save_selection_index(self, directory: str, index: int = None) -> None:
        """
        Save the current selection index for a directory.
        
        Args:
            directory: Directory path
            index: Index to save (if None, uses current index from calling context)
        """
        with self.state_lock:
            # Only save if index is explicitly provided
            if index is not None:
                self.state['last_selected_indices'][directory] = index

    def set_selection_index(self, index: int, directory: str = None) -> None:
        """
        Set the selection index for the specified directory.
        
        Args:
            index: Selection index to save
            directory: Directory path (defaults to current directory)
        """
        with self.state_lock:
            dir_path = directory or self.state['current_directory']
            self.state['last_selected_indices'][dir_path] = index
    
    def add_favorite(self, name: str, path: str = None) -> bool:
        """
        Add a favorite directory.
        
        Args:
            name: Name for the favorite
            path: Directory path (defaults to current directory)
            
        Returns:
            Success status
        """
        with self.state_lock:
            dir_path = path or self.state['current_directory']
            
            # Verify the path exists
            if not Path(dir_path).exists() or not Path(dir_path).is_dir():
                return False
                
            # Add to favorites
            self.state['favorites'][name] = dir_path
            
            # Save state
            if not self.auto_save:
                self._save_state()
                
            return True
    
    def remove_favorite(self, name: str) -> bool:
        """
        Remove a favorite directory.
        
        Args:
            name: Name of the favorite to remove
            
        Returns:
            Success status
        """
        with self.state_lock:
            if name in self.state['favorites']:
                del self.state['favorites'][name]
                
                # Save state
                if not self.auto_save:
                    self._save_state()
                    
                return True
            return False
    
    def get_favorites(self) -> Dict[str, str]:
        """Get all favorite directories."""
        with self.state_lock:
            return dict(self.state['favorites'])
    
    def navigate_to_favorite(self, name: str) -> bool:
        """
        Navigate to a favorite directory.
        
        Args:
            name: Name of the favorite
            
        Returns:
            Success status
        """
        with self.state_lock:
            if name in self.state['favorites']:
                return self.change_directory(self.state['favorites'][name])
            return False
    
    def get_history(self) -> List[str]:
        """Get the directory navigation history."""
        with self.state_lock:
            return list(self.state['history'])
    
    def get_history_position(self) -> int:
        """Get the current position in the directory history."""
        with self.state_lock:
            return self.state['history_position']
    
    def _begin_transaction(self, operation: str, details: Dict = None) -> int:
        """Begin a new transaction and log it."""
        with self.state_lock:
            self.transaction_id += 1
            transaction = {
                'id': self.transaction_id,
                'operation': operation,
                'details': details or {},
                'start_time': time.time(),
                'start_directory': self.state['current_directory'],
                'status': 'in_progress'
            }
            self.transaction_log.append(transaction)
            
            # Trim log if needed
            if len(self.transaction_log) > self.max_log_entries:
                self.transaction_log = self.transaction_log[-self.max_log_entries:]
                
            return self.transaction_id
    
    def _end_transaction(self, transaction_id: int, success: bool, 
                         message: str = None) -> None:
        """End a transaction and update its status."""
        with self.state_lock:
            # Find the transaction
            for transaction in self.transaction_log:
                if transaction['id'] == transaction_id:
                    transaction['end_time'] = time.time()
                    transaction['end_directory'] = self.state['current_directory']
                    transaction['status'] = 'success' if success else 'failed'
                    if message:
                        transaction['message'] = message
                    break
    
    def get_transaction_log(self, limit: int = None) -> List[Dict]:
        """
        Get the transaction log for debugging and recovery.
        
        Args:
            limit: Maximum number of transactions to return (newest first)
            
        Returns:
            List of transaction records
        """
        with self.state_lock:
            if limit:
                return list(reversed(self.transaction_log[-limit:]))
            return list(reversed(self.transaction_log))
    
    def save_now(self) -> None:
        """Explicitly save the current state."""
        self._save_state()
    
    def shutdown(self) -> None:
        """Shutdown the state manager and save state."""
        logger.info("Shutting down directory state manager...")
        
        # Signal auto-save thread to stop
        self._shutdown_flag.set()
        
        # Wait for auto-save thread to finish
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=1.0)
        
        # Final state save
        self._save_state()
        
        logger.info("Directory state manager shut down.")
