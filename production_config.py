"""
Production Configuration Helper for Railway Deployment
Ensures proper paths and settings for Railway production environment
"""
import os
import sys
from pathlib import Path

def setup_production_environment(project_root=None):
    """
    Configure environment for Railway production deployment
    
    Args:
        project_root: Absolute path to project root (auto-detected on Railway)
    """
    if project_root is None:
        project_root = os.getcwd()  # Railway sets this automatically
    
    # Set environment variables for production
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('DEBUG', 'False')
    
    # Railway handles database path automatically
    if not os.getenv('DATABASE_PATH'):
        os.environ['DATABASE_PATH'] = os.path.join(project_root, 'stocks.db')
    
    # Set collection interval for production (30 minutes)
    os.environ.setdefault('STOCKHARK_COLLECTION_INTERVAL', '30')
    
    # Add project paths to Python path
    src_dir = os.path.join(project_root, 'src')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

def validate_production_config():
    """
    Validate that all required configuration is present for production
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Check required environment variables
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET', 
        'REDDIT_USER_AGENT',
        'SECRET_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check database path is absolute
    db_path = os.getenv('DATABASE_PATH')
    if db_path and not os.path.isabs(db_path):
        errors.append(f"DATABASE_PATH should be absolute path, got: {db_path}")
    
    # Check Flask is in production mode
    if os.getenv('FLASK_ENV') != 'production':
        errors.append("FLASK_ENV should be 'production'")
    
    if os.getenv('DEBUG', 'False').lower() == 'true':
        errors.append("DEBUG should be False in production")
    
    return len(errors) == 0, errors

def get_production_info():
    """Get production configuration information for debugging"""
    return {
        'flask_env': os.getenv('FLASK_ENV'),
        'debug': os.getenv('DEBUG'), 
        'database_path': os.getenv('DATABASE_PATH'),
        'collection_interval': os.getenv('STOCKHARK_COLLECTION_INTERVAL'),
        'python_path': sys.path[:3],  # First 3 entries
        'reddit_configured': bool(os.getenv('REDDIT_CLIENT_ID')),
        'secret_key_set': bool(os.getenv('SECRET_KEY'))
    }