# test_helpers.py
import sys
import os
from pathlib import Path

def ensure_modules_importable():
    """
    Ensure that the required modules are in the Python import path.
    """
    # Get the project root directory (assuming this file is in the project root)
    project_root = Path(__file__).parent.absolute()
    
    # Add the project root to sys.path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"Added {project_root} to Python import path")
    
    # Check that required modules exist
    required_modules = [
        'gesture_signature_extractor.py',
        'gesture_recognition_engine.py',
        'gesture_signature_config_manager.py'
    ]
    
    missing_modules = []
    for module in required_modules:
        module_path = project_root / module
        if not module_path.exists():
            missing_modules.append(module)
    
    if missing_modules:
        print(f"Warning: The following modules are still missing: {', '.join(missing_modules)}")
    else:
        print("All required modules found in the project directory.")
