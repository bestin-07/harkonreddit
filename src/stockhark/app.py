"""
StockHark Flask Application Factory
Refactored application with blueprint architecture for better organization
"""

from flask import Flask
from flask_mail import Mail
import atexit

from .core.data import init_db
from .core.services import ServiceFactory, get_service_factory
from .core.services import BackgroundDataCollector, start_background_collection, stop_background_collection
from .web.routes import web_bp, api_bp

def create_app(config=None):
    """
    Application factory pattern for creating Flask app with proper configuration
    
    Args:
        config: Configuration dictionary or object
        
    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app with proper template/static folder configuration
    app = Flask(__name__, 
               template_folder='web/templates',
               static_folder='web/static')
    
    # Load configuration
    if config:
        app.config.update(config)
    
    # Initialize extensions
    mail = Mail(app)
    
    # Initialize database
    init_db()
    
    # Initialize services using ServiceFactory
    factory = get_service_factory()
    
    # Store service factory in app context for access in routes
    app.service_factory = factory
    app.mail = mail
    
    # Register blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    
    # Start background data collection
    print("🔄 Starting background data collection...")
    start_background_collection()
    print("✅ Background data collection started")
    
    # Register shutdown handler
    atexit.register(shutdown_background_services)
    
    return app

def shutdown_background_services():
    """Shutdown background services gracefully"""
    print("🛑 Shutting down background services...")
    stop_background_collection()
    print("✅ Background services stopped")

def create_production_app():
    """Create app configured for production deployment"""
    print("🚀 Initializing StockHark with Background Data Collection")
    
    app = create_app()
    
    # Show startup info
    from .core.data import get_database_stats
    stats = get_database_stats()
    print(f"📊 Database: {stats['total_mentions']} mentions, {stats['unique_stocks']} stocks")
    print(f"🔄 Background collection active (30min intervals)")
    
    return app

# Maintain backward compatibility with direct execution
if __name__ == '__main__':
    try:
        flask_app = create_production_app()
        print(f"🌐 Starting server at http://127.0.0.1:5000")
        flask_app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down StockHark...")
        shutdown_background_services()