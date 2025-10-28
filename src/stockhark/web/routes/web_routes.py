"""
Web Routes Blueprint
Handles all HTML-rendering routes for the StockHark web interface
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import datetime

from ...core.database import add_subscriber, get_top_stocks

# Create blueprint
web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Main landing page showing top 10 hot stocks"""
    try:
        # Use 30-day window to capture historical data
        print(f"DEBUG: Calling get_top_stocks(limit=10, hours=720)")
        top_stocks = get_top_stocks(limit=10, hours=720)
        print(f"DEBUG: Got {len(top_stocks)} stocks for index")
        return render_template('index.html', stocks=top_stocks)
    except Exception as e:
        print(f"Error loading index: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', stocks=[])

@web_bp.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Email subscription page"""
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            try:
                add_subscriber(email)
                flash('Successfully subscribed! You will receive alerts about hot stocks.', 'success')
                return redirect(url_for('web.subscribe'))
            except Exception as e:
                flash('Error subscribing. Please try again.', 'error')
        else:
            flash('Please enter a valid email address.', 'error')
    
    return render_template('subscribe.html')

@web_bp.route('/methodology')
def methodology():
    """Sentiment analysis methodology explanation page"""
    return render_template('sentiment_methodology.html')

# Template context processor to make datetime available in templates
@web_bp.context_processor
def inject_now():
    return {'now': datetime.now()}