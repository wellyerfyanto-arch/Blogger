import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)

class PerformanceTracker:
    def __init__(self, db_path: str = "data/performance.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database untuk tracking performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Table untuk post performance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS post_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_url TEXT NOT NULL,
                    post_title TEXT NOT NULL,
                    publish_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table untuk SEO performance
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seo_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_url TEXT NOT NULL,
                    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    google_rank INTEGER,
                    search_impressions INTEGER,
                    search_clicks INTEGER,
                    ctr REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Performance database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    def track_post(self, post_url: str, post_title: str):
        """Mulai tracking untuk post baru"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO post_performance (post_url, post_title)
                VALUES (?, ?)
            ''', (post_url, post_title))
            
            conn.commit()
            conn.close()
            logger.info(f"Started tracking for post: {post_title}")
            
        except Exception as e:
            logger.error(f"Error tracking post: {str(e)}")
    
    def update_metrics(self, post_url: str, metrics: Dict):
        """Update performance metrics untuk post"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE post_performance 
                SET views = ?, clicks = ?, shares = ?, comments = ?
                WHERE post_url = ?
            ''', (
                metrics.get('views', 0),
                metrics.get('clicks', 0),
                metrics.get('shares', 0),
                metrics.get('comments', 0),
                post_url
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated metrics for: {post_url}")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
    
    def get_post_performance(self, post_url: str) -> Dict:
        """Dapatkan performance data untuk post tertentu"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM post_performance 
                WHERE post_url = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (post_url,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "post_url": result[1],
                    "post_title": result[2],
                    "publish_date": result[3],
                    "views": result[4],
                    "clicks": result[5],
                    "shares": result[6],
                    "comments": result[7],
                    "engagement_rate": self.calculate_engagement_rate(result[4], result[5], result[6], result[7])
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error getting post performance: {str(e)}")
            return {}
    
    def get_overall_stats(self) -> Dict:
        """Dapatkan overall performance statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total posts
            cursor.execute('SELECT COUNT(*) FROM post_performance')
            total_posts = cursor.fetchone()[0]
            
            # Total views
            cursor.execute('SELECT SUM(views) FROM post_performance')
            total_views = cursor.fetchone()[0] or 0
            
            # Average engagement
            cursor.execute('SELECT AVG(views), AVG(clicks), AVG(shares) FROM post_performance')
            avg_views, avg_clicks, avg_shares = cursor.fetchone()
            
            conn.close()
            
            return {
                "total_posts": total_posts,
                "total_views": total_views,
                "average_views": round(avg_views or 0, 1),
                "average_clicks": round(avg_clicks or 0, 1),
                "average_shares": round(avg_shares or 0, 1),
                "total_engagement": self.calculate_total_engagement(avg_views, avg_clicks, avg_shares)
            }
            
        except Exception as e:
            logger.error(f"Error getting overall stats: {str(e)}")
            return {}
    
    def calculate_engagement_rate(self, views: int, clicks: int, shares: int, comments: int) -> float:
        """Hitung engagement rate"""
        if views == 0:
            return 0.0
        
        total_engagement = clicks + shares + comments
        return round((total_engagement / views) * 100, 2)
    
    def calculate_total_engagement(self, views: float, clicks: float, shares: float) -> int:
        """Hitung total engagement"""
        return int((views or 0) + (clicks or 0) + (shares or 0))

# Global instance
performance_tracker = PerformanceTracker()

def track_performance(post_url: str, post_title: str):
    """Wrapper function untuk mulai tracking performance"""
    return performance_tracker.track_post(post_url, post_title)
