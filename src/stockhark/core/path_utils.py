"""
Path Utilities for StockHark

Centralized path management to eliminate repetitive sys.path manipulation
and provide consistent path resolution across the application.
"""

import sys
import os
from pathlib import Path
from typing import Optional, List

# Cache the project root to avoid repeated calculations
_PROJECT_ROOT: Optional[Path] = None
_SRC_DIR: Optional[Path] = None

def get_project_root() -> Path:
    """
    Get the project root directory
    
    Returns:
        Path: Absolute path to the project root directory
    """
    global _PROJECT_ROOT
    
    if _PROJECT_ROOT is None:
        # Start from current file and traverse up to find project root
        current = Path(__file__).parent
        while current.parent != current:
            # Look for project indicators
            if any((current / indicator).exists() for indicator in [
                'main.py', '.env', 'requirements.txt', '.git', 'setup.py'
            ]):
                _PROJECT_ROOT = current
                break
            current = current.parent
        else:
            # Fallback: assume we're in src/stockhark/core and go up 3 levels
            _PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    return _PROJECT_ROOT

def get_src_directory() -> Path:
    """
    Get the src directory path
    
    Returns:
        Path: Absolute path to the src directory
    """
    global _SRC_DIR
    
    if _SRC_DIR is None:
        _SRC_DIR = get_project_root() / "src"
        
        # Verify src directory exists
        if not _SRC_DIR.exists():
            # Fallback: create it or use project root
            _SRC_DIR = get_project_root()
    
    return _SRC_DIR

def setup_python_path() -> None:
    """
    Add src directory to Python path if not already present
    
    This eliminates the need for repeated sys.path.insert() calls
    throughout the codebase.
    """
    src_dir = str(get_src_directory())
    
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

def get_data_directory() -> Path:
    """
    Get the data directory path
    
    Returns:
        Path: Absolute path to the data directory
    """
    return get_src_directory() / "data"

def get_json_directory() -> Path:
    """
    Get the JSON data directory path
    
    Returns:
        Path: Absolute path to the JSON data directory
    """
    return get_data_directory() / "json"

def get_database_path() -> Path:
    """
    Get the database file path
    
    Returns:
        Path: Absolute path to the SQLite database file
    """
    return get_data_directory() / "stocks.db"

def get_logs_directory() -> Path:
    """
    Get the logs directory path, creating it if it doesn't exist
    
    Returns:
        Path: Absolute path to the logs directory
    """
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir

def get_scripts_directory() -> Path:
    """
    Get the scripts directory path
    
    Returns:
        Path: Absolute path to the scripts directory
    """
    return get_project_root() / "scripts"

def ensure_directory_exists(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path: The directory path (now guaranteed to exist)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path

def resolve_relative_path(relative_path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Resolve a relative path against a base directory
    
    Args:
        relative_path: Relative path string
        base_dir: Base directory (defaults to project root)
        
    Returns:
        Path: Absolute path
    """
    if base_dir is None:
        base_dir = get_project_root()
    
    return (base_dir / relative_path).resolve()

def get_path_info() -> dict:
    """
    Get information about all important paths
    
    Returns:
        dict: Dictionary containing path information
    """
    return {
        'project_root': str(get_project_root()),
        'src_directory': str(get_src_directory()),
        'data_directory': str(get_data_directory()),
        'json_directory': str(get_json_directory()),
        'database_path': str(get_database_path()),
        'logs_directory': str(get_logs_directory()),
        'scripts_directory': str(get_scripts_directory()),
        'python_path_configured': str(get_src_directory()) in sys.path
    }

def validate_paths() -> List[str]:
    """
    Validate that all critical paths exist
    
    Returns:
        List[str]: List of validation errors (empty if all valid)
    """
    errors = []
    
    # Check critical directories
    critical_paths = [
        ('Project Root', get_project_root()),
        ('Source Directory', get_src_directory()),
        ('Data Directory', get_data_directory()),
        ('JSON Directory', get_json_directory()),
        ('Scripts Directory', get_scripts_directory())
    ]
    
    for name, path in critical_paths:
        if not path.exists():
            errors.append(f"{name} does not exist: {path}")
        elif not path.is_dir():
            errors.append(f"{name} is not a directory: {path}")
    
    # Check for main.py in project root
    main_py = get_project_root() / "main.py"
    if not main_py.exists():
        errors.append(f"main.py not found in project root: {main_py}")
    
    return errors

# Convenience function for scripts
def setup_script_environment():
    """
    Setup environment for script execution
    
    This function:
    1. Adds src to Python path
    2. Ensures data directory exists
    3. Validates critical paths
    
    Raises:
        RuntimeError: If critical paths are missing
    """
    # Setup Python path
    setup_python_path()
    
    # Ensure data directory exists
    ensure_directory_exists(get_data_directory())
    ensure_directory_exists(get_json_directory())
    
    # Validate paths
    errors = validate_paths()
    if errors:
        error_msg = "Path validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise RuntimeError(error_msg)

if __name__ == "__main__":
    # When run directly, show path information
    import json
    print("StockHark Path Information:")
    print(json.dumps(get_path_info(), indent=2))
    
    # Validate paths
    errors = validate_paths()
    if errors:
        print("\nPath Validation Errors:")
        for error in errors:
            print(f"  ❌ {error}")
    else:
        print("\n✅ All paths validated successfully")