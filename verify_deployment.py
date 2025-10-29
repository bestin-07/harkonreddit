#!/usr/bin/env python3
"""
Pre-deployment verification script for StockHark
Run this locally or on Railway to verify your deployment is ready
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_project_structure():
    """Check that required files and directories exist"""
    print("\n📁 Checking project structure...")
    
    required_files = [
        'wsgi.py',
        'requirements.txt',
        'railway.json',
        'Procfile',
        'src/stockhark/app.py',
        'src/stockhark/core/data/__init__.py',
        'production_config.py'
    ]
    
    required_dirs = [
        'src/',
        'src/stockhark/',
        'src/stockhark/core/',
        'src/stockhark/web/',
        'venv/'
    ]
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ Missing: {file_path}")
            all_good = False
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ Missing directory: {dir_path}")
            all_good = False
    
    return all_good

def check_environment_variables():
    """Check required environment variables"""
    print("\n🔧 Checking environment variables...")
    
    required_vars = {
        'REDDIT_CLIENT_ID': 'Reddit API client ID',
        'REDDIT_CLIENT_SECRET': 'Reddit API client secret',
        'REDDIT_USER_AGENT': 'Reddit API user agent',
        'SECRET_KEY': 'Flask secret key'
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show first/last few characters for security
            if len(value) > 10:
                display_value = f"{value[:4]}...{value[-4:]}"
            else:
                display_value = "***"
            print(f"   ✅ {var} = {display_value}")
        else:
            print(f"   ❌ Missing: {var} ({description})")
            all_good = False
    
    return all_good

def check_dependencies():
    """Check that required packages are installed"""
    print("\n📦 Checking Python dependencies...")
    
    required_packages = [
        'flask',
        'praw',
        'torch',
        'transformers',
        'spacy',
        'nltk',
        'python-dotenv'
    ]
    
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ Missing: {package}")
            all_good = False
    
    # Check spaCy model
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print(f"   ✅ spacy model: en_core_web_sm")
    except OSError:
        print(f"   ❌ Missing spaCy model: en_core_web_sm")
        print(f"      Run: python -m spacy download en_core_web_sm")
        all_good = False
    
    return all_good

def check_database_setup():
    """Check database can be initialized"""
    print("\n🗃️  Checking database setup...")
    
    try:
        # Set up paths
        sys.path.insert(0, 'src')
        
        from stockhark.core.data import init_db, get_database_stats
        
        # Initialize database
        init_db()
        print("   ✅ Database initialization successful")
        
        # Get stats
        stats = get_database_stats()
        print(f"   📊 Current mentions: {stats['total_mentions']}")
        print(f"   📊 Unique stocks: {stats['unique_stocks']}")
        print(f"   📊 Database size: {stats['database_size_mb']:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def check_app_creation():
    """Check that Flask app can be created"""
    print("\n🌐 Checking Flask app creation...")
    
    try:
        sys.path.insert(0, 'src')
        from stockhark.app import create_production_app
        
        app = create_production_app()
        print("   ✅ Flask app creation successful")
        
        # Check routes
        with app.app_context():
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            print(f"   📋 Routes registered: {len(routes)}")
            print(f"   📋 Sample routes: {routes[:5]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Flask app error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all deployment checks"""
    print("� StockHark Railway Deployment Verification")
    print("=" * 55)
    
    checks = [
        ("Python version", check_python_version),
        ("Project structure", check_project_structure),
        ("Environment variables", check_environment_variables),
        ("Dependencies", check_dependencies),
        ("Database setup", check_database_setup),
        ("Flask app creation", check_app_creation)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"   ❌ Error running {check_name} check: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 55)
    print("📋 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 55)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL CHECKS PASSED!")
        print("Your StockHark deployment is ready for Railway!")
        print("\nNext steps:")
        print("1. Push your code to GitHub")
        print("2. Connect GitHub repo to Railway")
        print("3. Set environment variables in Railway dashboard")
        print("4. Deploy automatically triggers")
        print("5. Visit your app at the Railway-provided URL")
    else:
        print(f"\n⚠️  {total-passed} ISSUES FOUND")
        print("Please fix the issues above before deploying.")
        print("Check the DEPLOYMENT_GUIDE.md for detailed instructions.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)