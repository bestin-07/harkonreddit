# StockHark Railway Deployment Guide

## � Complete Railway Deployment Instructions

### Step 1: Railway Account Setup
1. Create a free account at [Railway.app](https://railway.app)
2. Sign in with your GitHub account (recommended)
3. You get $5 in credits monthly on the free plan

### Step 2: Prepare Your GitHub Repository
1. **Push your code to GitHub** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial StockHark commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/stockhark.git
   git push -u origin main
   ```

2. **Ensure all files are committed**:
   - `railway.json`
   - `Procfile` 
   - `requirements.txt`
   - `wsgi.py`
   - All source code

### Step 3: Connect to Railway
1. Go to [Railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your StockHark repository
5. Railway will automatically detect it's a Python project

**Railway automatically handles dependency installation!** 

The build process will:
1. Detect `requirements.txt` and install all dependencies
2. Run `railway-build.sh` to download spaCy models
3. Set up the environment automatically

No manual installation needed! 🎉

### Step 4: Configure Environment Variables in Railway
1. In your Railway project dashboard, go to the **"Variables"** tab
2. Add the following environment variables:

   **Required Variables:**
   ```
   SECRET_KEY = your-very-secure-secret-key-here
   REDDIT_CLIENT_ID = your_reddit_client_id  
   REDDIT_CLIENT_SECRET = your_reddit_client_secret
   REDDIT_USER_AGENT = StockHark/1.0 by YourRedditUsername
   ```
   
   **Optional Variables:**
   ```
   STOCKHARK_COLLECTION_INTERVAL = 30
   FLASK_ENV = production
   DEBUG = False
   ```

### Step 5: Set Up Reddit API Access
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill out the form:
   - **Name**: StockHark
   - **Type**: Script
   - **Description**: Stock sentiment analysis
   - **About URL**: (leave blank)
   - **Redirect URI**: http://localhost
4. Copy the Client ID and Secret to your `.env` file

### Step 6: Deploy! 🚀
1. **Railway automatically deploys** when you connect the repo
2. Watch the build logs in real-time
3. Railway will:
   - Install dependencies from `requirements.txt`
   - Run the build script to download models
   - Start your app using the `Procfile`

### Step 7: Get Your Live URL
1. Once deployment completes, Railway provides a live URL
2. Click on your project → **"Settings"** → **"Domains"**
3. Your app will be available at something like: `https://stockhark-production-xxxx.up.railway.app`

### Step 8: Monitor Your Deployment
**Railway Dashboard provides:**
- 📊 Real-time metrics (CPU, memory, requests)
- 📋 Build and application logs  
- 💰 Usage and billing information
- 🔧 Easy environment variable management

### Step 9: Verify Everything Works
Visit your Railway URL and check:
- ✅ Homepage loads with stock data
- ✅ Stock details modals work
- ✅ Background data collection is running
- ✅ No error messages in Railway logs

## 🔧 Railway Features & Benefits

### Automatic Scaling
- Railway automatically scales based on traffic
- No manual configuration needed
- Handles traffic spikes seamlessly

### Database Persistence  
- Railway provides persistent storage for your SQLite database
- Data survives deployments and restarts
- Automatic backups available

### Background Tasks
- Your background data collection runs 24/7
- No additional configuration needed
- Collects Reddit data every 30 minutes automatically

### Performance & Limits
- **Free Plan**: $5 credit monthly (usually enough for small apps)
- **Starter Plan**: $20/month for more resources
- Excellent performance and uptime
- Global CDN included

## 🚨 Troubleshooting

### Common Issues:

1. **Build Failures**
   - Check Railway build logs for specific errors
   - Ensure `requirements.txt` is properly formatted  
   - Verify all dependencies are compatible

2. **Environment Variable Issues**
   - Double-check variable names in Railway dashboard
   - Ensure no extra spaces in values
   - Verify Reddit API credentials are correct

3. **App Won't Start**
   - Check Railway application logs
   - Verify `wsgi.py` and `Procfile` are correct
   - Ensure port binding is working (`$PORT` variable)

4. **Background Collection Not Working**
   - Check application logs for error messages
   - Verify Reddit API rate limits aren't exceeded
   - Ensure database can be written to

### Debugging Steps:
1. **Check Build Logs**: Railway → Project → "Deployments" tab
2. **Check App Logs**: Railway → Project → "Logs" tab  
3. **Test Locally**: Run `python verify_deployment.py`
4. **Monitor Resources**: Check Railway metrics dashboard

## 📊 Monitoring Your App

### Check Application Status
```bash
cd ~/stockhark
source venv/bin/activate
python -c "
from src.stockhark.core.data import get_database_stats
stats = get_database_stats()
print(f'📊 Total mentions: {stats[\"total_mentions\"]}')
print(f'🎯 Unique stocks: {stats[\"unique_stocks\"]}') 
print(f'💾 Database size: {stats[\"database_size_mb\"]:.2f} MB')
"
```

### Update Your Application
```bash
# Make changes locally
git add .
git commit -m "Update StockHark"
git push origin main

# Railway automatically redeploys!
```
**That's it!** Railway automatically detects the push and redeploys. 🚀

## 🎉 Success!

Your StockHark application will be live at your Railway-provided URL:
**https://stockhark-production-xxxx.up.railway.app**

Features available:
- ✅ Real-time stock sentiment analysis
- ✅ Interactive web dashboard  
- ✅ Background Reddit data collection
- ✅ FinBERT AI sentiment analysis
- ✅ Multi-source aggregation
- ✅ Responsive design

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review PythonAnywhere error logs
3. Test components individually using the provided scripts
4. Ensure all environment variables are correctly set

**Happy deploying! 🚀**