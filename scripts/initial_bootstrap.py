#!/usr/bin/env python3
"""
Initial Bootstrap Script for Railway Deployment

Runs data collection on first deployment to populate the database
with initial stock sentiment data before starting the web server.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_database_populated():
    """Check if database already has sufficient data"""
    try:
        from src.stockhark.core.data.database import get_database_stats
        stats = get_database_stats()
        total_mentions = stats.get('total_mentions', 0)
        unique_stocks = stats.get('unique_stocks', 0)
        
        print(f"📊 Current database stats: {total_mentions} mentions, {unique_stocks} stocks")
        
        # Consider database populated if we have reasonable amount of data
        return total_mentions >= 100 and unique_stocks >= 10
        
    except Exception as e:
        print(f"⚠️ Error checking database: {e}")
        return False

def run_initial_collection():
    """Run initial data collection for bootstrap"""
    print("🚀 Starting initial data collection for Railway deployment...")
    
    try:
        # Import the collection function
        from scripts.collect_data import collect_fresh_data
        
        # Run collection for 15 minutes with more posts per subreddit
        print("📡 Collecting data for 15 minutes...")
        collect_fresh_data(duration_minutes=15, posts_per_subreddit=25)
        
        print("✅ Initial bootstrap collection completed!")
        return True
        
    except Exception as e:
        print(f"❌ Bootstrap collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main bootstrap function"""
    print("=" * 60)
    print("🏗️  RAILWAY DEPLOYMENT BOOTSTRAP")
    print("=" * 60)
    
    # Check if this is the first deployment or database is empty
    if check_database_populated():
        print("✅ Database already populated, skipping bootstrap collection")
        print("🚀 Starting web server...")
        return
    
    print("📦 Database appears empty, running initial collection...")
    
    # Set environment variable to disable heavy FinBERT during bootstrap
    # This makes the initial collection much faster and lighter on CPU
    os.environ['STOCKHARK_BOOTSTRAP_MODE'] = 'true'
    
    # Run the initial collection
    success = run_initial_collection()
    
    if success:
        # Verify we got some data
        if check_database_populated():
            print("🎉 Bootstrap successful! Database now populated.")
        else:
            print("⚠️ Bootstrap completed but database still appears empty")
    else:
        print("❌ Bootstrap failed, but continuing with web server startup...")
    
    print("🚀 Starting web server...")
    print("=" * 60)

if __name__ == "__main__":
    main()