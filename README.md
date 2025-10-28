# 🚀 StockHark - Reddit Stock Sentiment Analyzer

A modern Flask web application that monitors Reddit for stock mentions and performs AI-powered sentiment analysis with automated background data collection. Built with professional architecture and clean UI design.

## ✨ Features

- **🤖 Background Data Collection** - Automated Reddit monitoring every 30 minutes using threading
- **🧠 FinBERT AI Sentiment Analysis** - Advanced transformer-based financial sentiment analysis with fallback to rule-based methods
- **📊 Professional Dashboard** - Clean, modern interface with real-time stock sentiment tracking
- **� SQLite Database** - Efficient local storage with 1,500+ stock mentions and 200+ unique stocks
- **🎯 Smart Stock Validation** - 4,200+ stock symbols with O(1) hash lookup validation
- **� RESTful API** - Complete API endpoints for stock data, status monitoring, and system health
- **🔄 No Refresh Needed** - Background updates eliminate manual refresh requirements
- **📱 Responsive Design** - Mobile-first design with professional color scheme
- **⚡ High Performance** - Optimized database queries and efficient data processing

## 🎯 Demo

**Homepage**: Shows top 10 trending stocks with sentiment indicators
**Email Alerts**: Subscribe to get notifications about hot stocks
**Clean UI**: Modern, aesthetic design with proper color theory

## 🛠 Technology Stack

- **Backend**: Flask with modular architecture, Python 3.8+
- **Database**: SQLite with optimized schema and indexing
- **Reddit API**: PRAW (Python Reddit API Wrapper) with direct authentication
- **AI/ML**: FinBERT transformer model (ProsusAI/finbert) with rule-based fallback
- **Background Processing**: Threading-based data collection with graceful shutdown
- **Stock Validation**: 4,200+ symbols with JSON-based O(1) lookup
- **Frontend**: Modern HTML5/CSS3 with responsive design and professional styling
- **Architecture**: Clean separation of concerns with core/, web/, and scripts/ modules

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/stockhark.git
cd stockhark
```

### 2. Set Up Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Reddit API

Copy `.env.example` to `.env` and add your Reddit API credentials:

```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret  
REDDIT_USER_AGENT=StockHark/1.0 by YourUsername
```

Get credentials at: https://www.reddit.com/prefs/apps

### 5. Run StockHark

```bash
python main.py
```

Visit `http://127.0.0.1:5000` to access your StockHark dashboard!

### 6. Optional: Manual Data Collection

```bash
python scripts/manual_collect.py
```

This runs a 15-minute Reddit collection session for immediate data.

## 🏗️ Architecture

```
StockHark/
├── main.py                           # Main entry point
├── src/stockhark/
│   ├── app.py                       # Flask application with background collection
│   ├── core/                        # Core business logic
│   │   ├── background_collector.py  # Automated 30-min data collection
│   │   ├── database.py              # SQLite operations with optimization
│   │   ├── enhanced_sentiment.py    # FinBERT + rule-based sentiment
│   │   └── validator.py             # Stock symbol validation (4,200+ symbols)
│   └── web/                         # Web interface
│       ├── templates/               # HTML templates (no refresh needed)
│       └── static/                  # CSS/JS assets
├── scripts/                         # Manual collection utilities
│   ├── manual_collect.py            # 15-minute collection script
│   └── collect_fresh_data.py        # Batch data collection
└── src/data/json/                   # Stock symbol databases
```

## 📊 Current Database Stats

- **1,500+ Stock Mentions** tracked from Reddit
- **200+ Unique Stocks** across all markets  
- **4,200+ Stock Symbols** validated (US/International)
- **1.7MB Database** with optimized indexing
- **Background Collection** every 30 minutes automatically

## 🔧 Configuration

### Reddit API Setup

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"  
3. Choose "script" as the app type
4. Note your client ID and secret
5. Set user agent like "StockHark/1.0 by YourUsername"

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Google account
2. Generate an [App Password](https://support.google.com/accounts/answer/185833)
3. Use this app password in your `.env` file

### Monitored Subreddits (67+ Total)

**Primary US Markets (8)**: wallstreetbets, stocks, investing, SecurityAnalysis, ValueInvesting, dividends, StockMarket, financialindependence

**European Markets (11)**: EuropeFIRE, UKInvesting, UKPersonalFinance, eupersonalfinance, Finanzen, france, italy, spain, investing_discussion, SecurityAnalysisEU, EuropeanOptions

**International (8)**: CanadianInvestor, AusFinance, IndiaInvestments, JapanFinance, AsianStocks, EmergingMarkets, GlobalMarkets, WorldNews

**Trading & Options (8)**: options, thetagang, daytrading, SwingTrading, pennystocks, RobinHood, smallstreetbets

**Technology (7)**: technology, artificial, MachineLearning, singularity, Futurology, startups, entrepreneur

**Commodities (8)**: Gold, SilverSqueeze, oil, energy, mining, uranium, solar, CleanEnergy  

**Real Estate (5)**: RealEstate, REITs, realestateinvesting, landlord, RealEstateCanada

You can modify categories in `enhanced_reddit_monitor.py`.

## 📊 How It Works

### 1. Reddit Monitoring
- Fetches hot posts from financial subreddits
- Extracts stock symbols using regex patterns
- Collects post metadata (score, comments, timestamps)

### 2. Sentiment Analysis
- Uses TextBlob for basic sentiment analysis
- Enhances with custom keyword analysis
- Bullish keywords: "buy", "long", "moon", "rocket"
- Bearish keywords: "sell", "short", "crash", "dump"

### 3. Alert System
- Triggers when stocks meet criteria:
  - 10+ mentions in 1 hour
  - Sentiment score > ±0.3
  - Multiple unique posts
- Sends styled HTML emails to subscribers

### 4. Data Storage
- SQLite database with two main tables:
  - `subscribers`: Email addresses
  - `stock_data`: Mentions, sentiment, timestamps

## 🎨 Design Philosophy

### Color Theory
- **Primary**: `#667eea` - Modern blue-purple gradient
- **Secondary**: `#764ba2` - Complementary purple
- **Success/Bullish**: `#38a169` - Positive green
- **Error/Bearish**: `#e53e3e` - Alert red
- **Neutral**: `#718096` - Balanced gray

### UI/UX Principles
- **Minimalistic**: Clean, uncluttered interface
- **Responsive**: Mobile-first design approach
- **Accessible**: High contrast ratios and clear typography
- **Fast**: Optimized loading and smooth animations

## 🌐 Deployment on PythonAnywhere

### 1. Upload Files
Upload your project files to PythonAnywhere via the Files tab.

### 2. Install Dependencies
In a PythonAnywhere Bash console:
```bash
pip3.10 install --user -r requirements.txt
python3.10 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 3. Configure Web App
1. Go to the Web tab in your PythonAnywhere dashboard
2. Add a new web app (Flask, Python 3.10)
3. Set the source code path to your project directory
4. Set the WSGI configuration file to `/home/yourusername/reddit-stock-monitor/wsgi.py`

### 4. Set Environment Variables
In the Web tab, add your environment variables in the "Environment variables" section.

### 5. Schedule Monitoring
In the Tasks tab, create a scheduled task to run monitoring:
```bash
python3.10 /home/yourusername/reddit-stock-monitor/app.py
```

## 📈 API Endpoints

### GET /api/stocks
Returns top trending stocks with sentiment data.

**Parameters:**
- `hours` (optional): Time period to analyze (default: 24)
- `limit` (optional): Number of stocks to return (default: 10)

**Response:**
```json
[
  {
    "symbol": "GME",
    "mentions": 47,
    "avg_sentiment": 0.65,
    "overall_sentiment": "bullish",
    "unique_posts": 23,
    "latest_mention": "2024-10-27T15:30:00"
  }
]
```

### POST /api/refresh
Triggers manual data refresh.

## 🔒 Security Notes

- Never commit API keys to version control
- Use environment variables for all secrets
- Implement rate limiting for API endpoints
- Validate all user inputs
- Use HTTPS in production

## 🐛 Troubleshooting

### Common Issues

**Reddit API Rate Limiting**
- Implement delays between requests
- Check your API credentials
- Ensure proper user agent

**Email Not Sending**
- Verify Gmail app password
- Check spam folder
- Ensure proper SMTP settings

**Sentiment Analysis Accuracy**
- Review stock symbol extraction regex
- Adjust bullish/bearish keywords
- Consider training custom ML models

## 🚀 Future Enhancements

- [ ] Integration with stock price APIs (Yahoo Finance, Alpha Vantage)
- [ ] Historical sentiment tracking and charts
- [ ] User dashboard with personalized watchlists
- [ ] Social media expansion (Twitter, Discord)
- [ ] Machine learning sentiment models
- [ ] Real-time WebSocket updates
- [ ] Mobile app with push notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**This is not financial advice.** The information provided by StockHark is for educational and informational purposes only. It should not be considered as financial advice or a recommendation to buy or sell any securities. Always do your own research and consult with a qualified financial advisor before making investment decisions.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/reddit-stock-monitor/issues)
- **Email**: your-email@gmail.com
- **Documentation**: This README and the `.copilot` file

---

Made with ❤️ by [Your Name] | Powered by Reddit API & Flask