#!/usr/bin/env python3
"""
Enhanced Reddit Monitor with Extended Subreddit Coverage
Monitors a comprehensive list of financial subreddits for global stock coverage
"""

import praw
from datetime import datetime, timedelta
import os
import re
from ..core.reddit_client import get_reddit_client

class EnhancedRedditMonitor:
    """Enhanced Reddit API monitor with broader subreddit coverage"""
    
    def __init__(self):
        self.reddit = get_reddit_client()
        
        # Comprehensive subreddit list for global stock coverage
        self.financial_subreddits = {
            # Main US Markets
            'primary_us': [
                'wallstreetbets', 'stocks', 'investing', 'SecurityAnalysis',
                'ValueInvesting', 'dividends', 'StockMarket', 'financialindependence'
            ],
            
            # Specific Stock Communities
            'stock_specific': [
                'GME', 'amcstock', 'PLTR', 'NIO', 'TSLA', 'AAPL', 'AMD', 'NVDA',
                'Bitcoin', 'CryptoCurrency', 'ethtrader', 'dogecoin'
            ],
            
            # European Markets
            'european': [
                'EuropeFIRE', 'UKInvesting', 'UKPersonalFinance', 'eupersonalfinance',
                'Finanzen', 'france', 'italy', 'spain', 'investing_discussion',
                'SecurityAnalysisEU', 'EuropeanOptions'
            ],
            
            # International Markets
            'international': [
                'CanadianInvestor', 'AusFinance', 'IndiaInvestments', 'JapanFinance',
                'AsianStocks', 'EmergingMarkets', 'GlobalMarkets', 'WorldNews'
            ],
            
            # Trading & Options
            'trading': [
                'options', 'thetagang', 'SecurityAnalysis', 'daytrading',
                'SwingTrading', 'pennystocks', 'RobinHood', 'smallstreetbets'
            ],
            
            # Technology & Innovation
            'tech_focused': [
                'technology', 'artificial', 'MachineLearning', 'singularity',
                'Futurology', 'startups', 'entrepreneur'
            ],
            
            # Commodities & Energy
            'commodities': [
                'Gold', 'SilverSqueeze', 'oil', 'energy', 'mining',
                'uranium', 'solar', 'CleanEnergy'
            ],
            
            # REITs & Real Estate
            'real_estate': [
                'RealEstate', 'REITs', 'realestateinvesting',
                'landlord', 'RealEstateCanada'
            ]
        }
    
    def get_all_subreddits(self, category_filter=None):
        """Get list of subreddits to monitor based on category"""
        if category_filter:
            if isinstance(category_filter, str):
                return self.financial_subreddits.get(category_filter, [])
            elif isinstance(category_filter, list):
                subreddits = []
                for category in category_filter:
                    subreddits.extend(self.financial_subreddits.get(category, []))
                return subreddits
        
        # Return all subreddits
        all_subs = []
        for category, subs in self.financial_subreddits.items():
            all_subs.extend(subs)
        return all_subs
    
    def get_subreddit_stats(self):
        """Get statistics about monitored subreddits"""
        stats = {'total': 0}
        for category, subs in self.financial_subreddits.items():
            stats[category] = len(subs)
            stats['total'] += len(subs)
        return stats
    
    def get_enhanced_hot_posts(self, categories=None, limit=25):
        """
        Get hot posts from specified categories of subreddits
        
        Args:
            categories (list): List of category names to monitor
            limit (int): Number of posts per subreddit
        
        Returns:
            list: List of post dictionaries with enhanced metadata
        """
        if categories is None:
            categories = ['primary_us', 'european', 'trading']
        
        subreddits = self.get_all_subreddits(categories)
        posts = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for post in subreddit.hot(limit=limit):
                    # Skip stickied posts
                    if post.stickied:
                        continue
                    
                    # Enhanced post data collection
                    content = post.selftext if hasattr(post, 'selftext') else ''
                    
                    # Get more comments for better context
                    post.comments.replace_more(limit=10)
                    top_comments = []
                    
                    # Get up to 15 top comments
                    for comment in post.comments[:15]:
                        if hasattr(comment, 'body') and len(comment.body) > 10:
                            # Filter out very short comments
                            top_comments.append(comment.body)
                    
                    # Calculate engagement score
                    engagement_score = (post.score * 0.7) + (post.num_comments * 0.3)
                    
                    # Detect potential stock symbols in title (quick check)
                    title_upper = post.title.upper()
                    potential_stocks = len(re.findall(r'\b[A-Z]{2,5}\b', title_upper))
                    
                    posts.append({
                        'id': post.id,
                        'title': post.title,
                        'content': content,
                        'comments': top_comments,
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'created_utc': datetime.fromtimestamp(post.created_utc),
                        'url': f"https://reddit.com{post.permalink}",
                        'subreddit': subreddit_name,
                        'subreddit_category': self._get_subreddit_category(subreddit_name),
                        'author': str(post.author) if post.author else '[deleted]',
                        'engagement_score': engagement_score,
                        'potential_stock_count': potential_stocks,
                        'flair': post.link_flair_text if hasattr(post, 'link_flair_text') else None
                    })
                    
            except Exception as e:
                print(f"Error fetching posts from r/{subreddit_name}: {e}")
                continue
        
        # Sort by engagement score
        posts.sort(key=lambda x: x['engagement_score'], reverse=True)
        return posts
    
    def get_trending_by_region(self, region='us', hours_back=24):
        """
        Get trending posts by geographical region
        
        Args:
            region (str): 'us', 'eu', 'asia', 'global'
            hours_back (int): Hours to look back
        
        Returns:
            list: Trending posts from specified region
        """
        region_mapping = {
            'us': ['primary_us', 'trading', 'stock_specific'],
            'eu': ['european'],
            'asia': ['international'],  # Subset of international focusing on Asia
            'global': ['primary_us', 'european', 'international', 'trading']
        }
        
        categories = region_mapping.get(region, ['primary_us'])
        posts = self.get_enhanced_hot_posts(categories, limit=15)
        
        # Filter by time
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_posts = [post for post in posts if post['created_utc'] >= cutoff_time]
        
        return recent_posts[:50]  # Return top 50
    
    def _get_subreddit_category(self, subreddit_name):
        """Get the category of a subreddit"""
        for category, subs in self.financial_subreddits.items():
            if subreddit_name in subs:
                return category
        return 'unknown'
    
    def get_subreddit_stats(self):
        """Get statistics about monitored subreddits"""
        stats = {}
        total_subs = 0
        
        for category, subs in self.financial_subreddits.items():
            stats[category] = len(subs)
            total_subs += len(subs)
        
        stats['total'] = total_subs
        return stats

# Backward compatibility - replace the old RedditMonitor
class RedditMonitor(EnhancedRedditMonitor):
    """Backward compatible Reddit monitor"""
    
    def get_hot_posts(self, subreddits, limit=100):
        """Legacy method for backward compatibility"""
        if isinstance(subreddits, list):
            # Use the enhanced method but filter to specific subreddits
            all_posts = self.get_enhanced_hot_posts(['primary_us', 'trading'], limit=limit)
            filtered_posts = [post for post in all_posts if post['subreddit'] in subreddits]
            return filtered_posts
        else:
            return self.get_enhanced_hot_posts(['primary_us'], limit=limit)