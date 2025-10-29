#!/usr/bin/env python3
"""
WSGI Configuration for StockHark on Railway
Railway deployment configuration for the Flask application.
"""

import sys
import os
from pathlib import Path

# Railway automatically sets the working directory to the project root
project_root = os.getcwd()

# Add src directory to Python path
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Set up Railway environment
def setup_railway_environment():
    """Configure environment for Railway deployment"""
    # Railway automatically provides PORT environment variable
    port = os.getenv('PORT', '8000')
    
    # Set production environment
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('DEBUG', 'False')
    
    # Railway provides a /tmp directory for temporary files
    # Database will be stored in the persistent volume
    if not os.getenv('DATABASE_PATH'):
        os.environ['DATABASE_PATH'] = os.path.join(project_root, 'stocks.db')
    
    # Set collection interval for production (30 minutes)
    os.environ.setdefault('STOCKHARK_COLLECTION_INTERVAL', '30')
    
    print(f"🚂 Railway environment configured - Port: {port}")
    return port

# Load environment variables
try:
    from dotenv import load_dotenv
    
    # Load .env file if it exists (for local development)
    env_file = os.path.join(project_root, '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print("✅ Environment variables loaded from .env file")
    
    # Railway automatically loads environment variables from the dashboard
    print("✅ Railway environment variables loaded")
    
except ImportError:
    print("⚠️  python-dotenv not available, using Railway environment variables only")

# Set up Railway environment
port = setup_railway_environment()

# Validate required environment variables
def validate_railway_config():
    """Validate Railway deployment configuration"""
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET', 
        'REDDIT_USER_AGENT',
        'SECRET_KEY'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Set these in Railway dashboard under 'Variables' tab")
        return False
    
    print("✅ All required environment variables present")
    return True

# Import and create the Flask application
try:
    # Validate configuration first
    config_valid = validate_railway_config()
    
    if not config_valid:
        raise ValueError("Missing required environment variables")
    
    # Download spaCy model if not already present
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("✅ spaCy model loaded")
    except OSError:
        print("📥 Downloading spaCy model...")
        os.system('python -m spacy download en_core_web_sm')
        print("✅ spaCy model downloaded")
    
    # Import the Flask app factory
    from stockhark.app import create_production_app
    
    # Create the WSGI application
    application = create_production_app()
    
    print("✅ StockHark WSGI application created successfully")
    print(f"🚂 Railway deployment ready on port {port}")
    
except Exception as e:
    print(f"❌ Error creating WSGI application: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal error application for debugging
    try:
        from flask import Flask, jsonify
        application = Flask(__name__)
        
        @application.route('/')
        def error():
            return f"""
            <h1>🚨 StockHark Railway Deployment Error</h1>
            <h2>Error Details:</h2>
            <p><strong>{str(e)}</strong></p>
            
            <h2>Railway Troubleshooting:</h2>
            <ol>
                <li>Check environment variables in Railway dashboard</li>
                <li>Verify build completed successfully</li>
                <li>Check Railway deployment logs</li>
                <li>Ensure all dependencies installed correctly</li>
            </ol>
            
            <h2>Configuration Info:</h2>
            <pre>
Project Root: {project_root}
Python Path: {sys.path[:3]}
PORT: {os.getenv('PORT', 'Not set')}
Environment Variables: {[k for k in os.environ.keys() if any(x in k for x in ['REDDIT', 'FLASK', 'SECRET', 'DATABASE'])]}
            </pre>
            
            <h2>Full Traceback:</h2>
            <pre>{traceback.format_exc()}</pre>
            """
        
        @application.route('/health')
        def health():
            return jsonify({
                "status": "error", 
                "message": str(e),
                "port": os.getenv('PORT'),
                "env_vars_present": bool(os.getenv('REDDIT_CLIENT_ID'))
            })
        
        print("🔧 Created Railway error application for debugging")
        
    except Exception as flask_error:
        print(f"❌ Could not create Flask app: {flask_error}")
        
        # Last resort WSGI application
        def application(environ, start_response):
            status = '500 Internal Server Error'
            headers = [('Content-Type', 'text/html')]
            start_response(status, headers)
            
            error_html = f"""
            <html><body>
            <h1>Critical Railway Deployment Error</h1>
            <p>Flask Error: {flask_error}</p>
            <p>Original Error: {e}</p>
            <p>Check Railway deployment logs for details.</p>
            <p>Project Root: {project_root}</p>
            </body></html>
            """
            return [error_html.encode('utf-8')]

# For local development
if __name__ == "__main__":
    print("� Running StockHark locally (Railway mode)")
    port = int(os.getenv('PORT', 8000))
    application.run(debug=False, host='0.0.0.0', port=port)