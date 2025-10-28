import praw
from datetime import datetime, timedelta
import os

# Import enhanced monitor
from .enhanced_reddit_monitor import EnhancedRedditMonitor

class RedditMonitor(EnhancedRedditMonitor):
    """Handles Reddit API interactions to fetch stock-related posts"""
    
    def __init__(self):
        # Call parent constructor which sets up the Reddit client
        super().__init__()
        
        # Legacy subreddits property for backward compatibility
        self.subreddits = self.get_all_subreddits('primary_us')
    
    def get_hot_posts(self, subreddits, limit=100):
        """
        Fetch hot posts from specified subreddits
        
        Args:
            subreddits (list): List of subreddit names
            limit (int): Number of posts to fetch per subreddit
        
        Returns:
            list: List of post dictionaries
        """
        posts = []
        
        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for post in subreddit.hot(limit=limit):
                    # Skip stickied posts
                    if post.stickied:
                        continue
                    
                    # Get post content
                    content = post.selftext if hasattr(post, 'selftext') else ''
                    
                    # Get top comments for additional context
                    post.comments.replace_more(limit=5)
                    top_comments = []
                    for comment in post.comments[:10]:  # Get top 10 comments
                        if hasattr(comment, 'body'):
                            top_comments.append(comment.body)
                    
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
                        'author': str(post.author) if post.author else '[deleted]'
                    })
                    
            except Exception as e:
                print(f"Error fetching posts from r/{subreddit_name}: {e}")
                continue
        
        return posts
    
    def get_trending_posts(self, subreddits, hours_back=24):
        """
        Get posts that are trending (high score relative to age)
        
        Args:
            subreddits (list): List of subreddit names
            hours_back (int): How many hours back to look
        
        Returns:
            list: List of trending post dictionaries
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        all_posts = self.get_hot_posts(subreddits)
        
        # Filter posts by time and calculate trending score
        trending_posts = []
        for post in all_posts:
            if post['created_utc'] >= cutoff_time:
                # Calculate trending score (score per hour)
                hours_old = (datetime.now() - post['created_utc']).total_seconds() / 3600
                if hours_old > 0:
                    trending_score = post['score'] / hours_old
                    post['trending_score'] = trending_score
                    trending_posts.append(post)
        
        # Sort by trending score
        trending_posts.sort(key=lambda x: x['trending_score'], reverse=True)
        
        return trending_posts[:50]  # Return top 50 trending posts