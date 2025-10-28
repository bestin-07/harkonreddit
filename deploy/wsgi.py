# WSGI file for PythonAnywhere deployment
import sys
import os

# Add your project directory to the Python path
project_home = 'C:\Users\antub\OneDrive - ABB\Documents\Bestin Codes\Reddit Hark'  # Update this path
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables (you can also set these in the PythonAnywhere dashboard)
# Generate a secure secret key: python -c "import secrets; print(secrets.token_hex(32))"
os.environ['SECRET_KEY'] = 'your-secret-key-change-this-to-something-secure'
# Get these from https://www.reddit.com/prefs/apps after creating a "script" type app
os.environ['REDDIT_CLIENT_ID'] = 'r5W6KA6rrKkDSutfMkp4OQ'
os.environ['REDDIT_CLIENT_SECRET'] = 'RphGwneeoqv6T-VUpeimORDc7_QTrg'
os.environ['REDDIT_USER_AGENT'] = 'StockHark/1.0 by /u/Far_Soup1744'
os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
os.environ['MAIL_PORT'] = '587'
os.environ['MAIL_USE_TLS'] = 'true'
os.environ['MAIL_USERNAME'] = 'your-email@gmail.com'
os.environ['MAIL_PASSWORD'] = 'your-app-password'
os.environ['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'

# Import your Flask application
from app import app as application

if __name__ == "__main__":
    application.run()