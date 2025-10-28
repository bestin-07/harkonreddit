#!/usr/bin/env python3
"""
StockHark - Reddit Stock Sentiment Monitor
Main entry point for the application
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from stockhark.app import app
from stockhark.config import FLASK_CONFIG

if __name__ == "__main__":
    print("🚀 Starting StockHark - Reddit Stock Sentiment Monitor")
    print(f"   📊 Database: {src_dir}/data/stocks.db")
    print(f"   🌐 Server: http://{FLASK_CONFIG['HOST']}:{FLASK_CONFIG['PORT']}")
    print("   📰 Monitoring Reddit for stock mentions...")
    
    app.run(
        host=FLASK_CONFIG['HOST'],
        port=FLASK_CONFIG['PORT'],
        debug=FLASK_CONFIG['DEBUG']
    )