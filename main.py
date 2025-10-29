#!/usr/bin/env python3
"""
StockHark - Main Entry Point
Reddit Stock Sentiment Analysis with Background Data Collection
"""

import os
import sys
from pathlib import Path

# Setup Python path using centralized utility
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Now we can import path utilities
from stockhark.core.path_utils import setup_python_path
setup_python_path()

def main():
    """Main entry point for StockHark application"""
    print(" Starting StockHark - Reddit Stock Sentiment Analyzer")
    print("=" * 60)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print(" Environment variables loaded")
    except ImportError:
        print("  python-dotenv not found, using system environment")
    
    # Check Reddit API configuration
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    if not reddit_client_id or reddit_client_id == 'your-client-id':
        print("\n Reddit API Configuration Required!")
        print(" Please set up your .env file with Reddit API credentials:")
        print("   REDDIT_CLIENT_ID=your_actual_client_id")
        print("   REDDIT_CLIENT_SECRET=your_actual_client_secret")
        print("   REDDIT_USER_AGENT=StockHark/1.0 by YourUsername")
        print("\n Get credentials at: https://www.reddit.com/prefs/apps")
        return False
    
    try:
        # Import and initialize database
        from stockhark.core.data import init_db, get_database_stats
        
        print(" Initializing database...")
        init_db()
        
        # Show current database status
        stats = get_database_stats()
        print(f"   Total mentions: {stats['total_mentions']}")
        print(f"   Unique stocks: {stats['unique_stocks']}")
        print(f"   Database size: {stats['database_size_mb']:.2f} MB")
        
        # Start the Flask application with background collection
        from stockhark.app import create_app
        
        print("\n Starting Flask web application...")
        print(" Access your StockHark dashboard at: http://127.0.0.1:5000")
        print(" Background data collection will start automatically")
        print("\n Press Ctrl+C to stop the application")
        print("=" * 60)
        
        # Create and run the app
        app = create_app()
        
        # Run with threading enabled for background collection
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n  StockHark stopped by user")
        print(" Thanks for using StockHark!")
        return True
        
    except ImportError as e:
        print(f"\n Import Error: {e}")
        print(" Make sure all required packages are installed")
        return False
        
    except Exception as e:
        print(f"\n Error starting StockHark: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n Fatal error: {e}")
        sys.exit(1)
