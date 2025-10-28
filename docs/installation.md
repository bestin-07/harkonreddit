# StockHark Installation Guide

## Prerequisites

- Python 3.8 or higher
- Reddit API credentials
- Git (optional)

## Installation Steps

### 1. Clone or Download the Project

```bash
git clone <your-repo-url>
cd stockhark
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

1. Copy `.env.example` to `.env`
2. Fill in your Reddit API credentials:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=StockHark/1.0
SECRET_KEY=your_secret_key
```

### 5. Initialize Database

```bash
python scripts/collect_data.py --setup
```

### 6. Run the Application

```bash
python main.py
```

Visit `http://localhost:5000` to access StockHark.

## Troubleshooting

- **Import Errors**: Make sure you're in the project root and virtual environment is activated
- **Database Errors**: Check if `src/data/stocks.db` exists and is readable
- **Reddit API Errors**: Verify your API credentials in `.env`