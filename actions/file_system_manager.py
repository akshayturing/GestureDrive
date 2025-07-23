# file_system_manager.py

import os
import pathlib
from pathlib import Path
import time
import threading
from typing import List, Dict, Any, Tuple

class FileSystemManager:
    """
    Manages file system navigation and operations through gesture control.
    Provides real-time tracking of the current working directory and
    allows gesture-based navigation between directories and files.
    """
    
    def __init__(self, initial_path: str = None):
        """
        Initialize the FileSystemManager with a starting directory.
        
        Args:
            initial_path (str, optional): The starting directory path. 
                                         Defaults to current working directory.
        """
        # Set initial directory
        self.current_path = Path(initial_path) if initial_path else Path.cwd()
        
        # Ensure the path exists and is a directory
        if not self.current_path.exists() or not self.current_path.is_dir():
            raise ValueError(f"Invalid directory path: {self.current_path}")
        
        # Directory contents cache
        self._dir_cache = {}
        self._cache_timestamp = 0
        self._cache_lock = threading.Lock()
        
        # Directory history for navigation
        self._history = [self.current_path]
        self._history_position = 0
        
        # File system change monitor
        self._monitor_running = False
        self._monitor_thread = None
        self._last_check_time = 0
        self._check_interval = 1.0  # seconds
        
    def start_monitoring(self) -> None:
        """Start the file system monitoring thread."""
        if self._monitor_running:
            return
            
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_changes, daemon=True)
        self._monitor_thread.start()
        
    def stop_monitoring(self) -> None:
        """Stop the file system monitoring thread."""
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            
    def _monitor_changes(self) -> None:
        """Monitor for file system changes in the current directory."""
        while self._monitor_running:
            current_time = time.time()
            
            # Check for changes at the specified interval
            if current_time - self._last_check_time >= self._check_interval:
                self._last_check_time = current_time
                self._update_cache_if_needed(force=True)
                
            time.sleep(0.1)  # Reduce CPU usage
    
    def get_current_path(self) -> Path:
        """Get the current working directory path."""
        return self.current_path
    
    def list_directory(self, path: str = None) -> List[Dict[str, Any]]:
        """
        List contents of a directory with details.
        
        Args:
            path (str, optional): The directory path to list. 
                                 Defaults to current directory.
                                 
        Returns:
            List of dictionaries with file/directory information
        """
        target_path = Path(path) if path else self.current_path
        
        if not target_path.exists() or not target_path.is_dir():
            raise ValueError(f"Invalid directory path: {target_path}")
            
        # Use cached results if available and recent
        if self._update_cache_if_needed(target_path):
            return self._dir_cache.get(str(target_path), [])
        
        # Gather directory contents with details
        contents = []
        try:
            for item in target_path.iterdir():
                # Skip hidden files and directories (starting with .)
                if item.name.startswith('.'):
                    continue
                    
                # Get file stats
                stats = item.stat()
                
                # Create item info dictionary
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'is_dir': item.is_dir(),
                    'size': stats
                    .st_size if item.is_file() else 0,
                    'modified': stats.st_mtime,
                    'created': stats.st_ctime,
                }
                
                contents.append(item_info)
                
            # Sort directories first, then files alphabetically
            contents.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            # Update cache
            with self._cache_lock:
                self._dir_cache[str(target_path)] = contents
                self._cache_timestamp = time.time()
                
            return contents
            
        except (PermissionError, OSError) as e:
            print(f"Error accessing directory {target_path}: {e}")
            return []
            
    def _update_cache_if_needed(self, path: Path = None, force: bool = False) -> bool:
        """
        Update the directory cache if needed.
        
        Args:
            path (Path, optional): The directory to check. Defaults to current directory.
            force (bool): Force update regardless of cache age
            
        Returns:
            bool: True if cache is valid, False if update was needed
        """
        target_path = path if path else self.current_path
        path_str = str(target_path)
        
        current_time = time.time()
        cache_age = current_time - self._cache_timestamp
        
        # Check if cache needs updating
        if force or cache_age > self._check_interval or path_str not in self._dir_cache:
            return False
        
        return True
        
    def navigate_to(self, path: str) -> bool:
        """
        Navigate to a new directory.
        
        Args:
            path (str): The target directory path
            
        Returns:
            bool: Success or failure
        """
        target = Path(path)
        
        # Verify the path exists and is a directory
        if not target.exists() or not target.is_dir():
            return False
            
        # Update current path and history
        self.current_path = target
        
        # Truncate forward history if navigating from middle
        if self._history_position < len(self._history) - 1:
            self._history = self._history[:self._history_position + 1]
            
        # Add new path to history if different from current
        if self._history[-1] != target:
            self._history.append(target)
            self._history_position = len(self._history) - 1
            
        return True
        
    def navigate_up(self) -> bool:
        """Navigate up one directory level."""
        parent = self.current_path.parent
        
        # Check if already at root
        if parent == self.current_path:
            return False
            
        return self.navigate_to(str(parent))
        
    def navigate_back(self) -> bool:
        """Navigate to previous directory in history."""
        if self._history_position <= 0:
            return False
            
        self._history_position -= 1
        self.current_path = self._history[self._history_position]
        return True
        
    def navigate_forward(self) -> bool:
        """Navigate to next directory in history."""
        if self._history_position >= len(self._history) - 1:
            return False
            
        self._history_position += 1
        self.current_path = self._history[self._history_position]
        return True
        
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific file.
        
        Args:
            filename (str): Name of the file in the current directory
            
        Returns:
            Dict with file information or None if file doesn't exist
        """
        file_path = self.current_path / filename
        
        if not file_path.exists():
            return None
            
        try:
            stats = file_path.stat()
            
            # Determine file type
            file_type = "directory" if file_path.is_dir() else "file"
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in ('.jpg', '.jpeg', '.png', '.gif', '.bmp'):
                    file_type = "image"
                elif suffix in ('.mp4', '.avi', '.mov', '.mkv'):
                    file_type = "video"
                elif suffix in ('.mp3', '.wav', '.ogg', '.flac'):
                    file_type = "audio"
                elif suffix in ('.txt', '.md', '.py', '.js', '.html', '.css'):
                    file_type = "text"
                    
            return {
                'name': file_path.name,
                'path': str(file_path),
                'type': file_type,
                'size': stats.st_size if file_path.is_file() else 0,
                'size_formatted': self._format_file_size(stats.st_size) if file_path.is_file() else "0 B",
                'modified': stats.st_mtime,
                'modified_formatted': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.st_mtime)),
                'created': stats.st_ctime,
                'created_formatted': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.st_ctime)),
            }
            
        except (PermissionError, OSError) as e:
            print(f"Error accessing file {file_path}: {e}")
            return None
            
    def _format_file_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"