import os
import requests
import json
import schedule
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import pandas as pd
from werkzeug.utils import secure_filename
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration for Render
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# Import modules dengan error handling
try:
    from content_generator import generate_article, research_keywords
    from image_generator import generate_image_prompt, create_image
    from blogger_integration import post_to_blogger
    from seo_analyzer import analyze_seo
    from plagiarism_checker import check_plagiarism
    from performance_tracker import track_performance
    from config_manager import ConfigManager
except ImportError as e:
    logger.warning(f"Some modules not available: {e}")
    
    # Fallback functions
    def generate_article(title, keywords=None):
        return {
            "title": title,
            "content": f"This is a sample article about {title}.",
            "meta_description": f"Learn about {title} in this comprehensive guide.",
            "keywords": keywords or [],
            "word_count": 100
        }
    
    def generate_image_prompt(title):
        return f"Image for {title}"
    
    def create_image(prompt):
        return None

# Default configuration
DEFAULT_CONFIG = {
    "posting_schedule": {
        "frequency": "daily",
        "time": "10:00",
        "days": ["monday", "wednesday", "friday"],
        "max_posts_per_day": 2
    },
    "content_settings": {
        "min_words": 1000,
        "max_words": 2000,
        "target_readability": "medium",
        "auto_research_keywords": True,
        "auto_generate_images": True,
        "plagiarism_check": True
    },
    "seo_settings": {
        "keyword_density_min": 0.5,
        "keyword_density_max": 2.5,
        "internal_links": True,
        "external_links": True,
        "meta_description_auto": True
    }
}

class AutoPostingSystem:
    def __init__(self):
        self.scheduled_posts = []
        self.posting_config = DEFAULT_CONFIG.copy()
        self.bulk_titles = []
        self.load_data()
        self.setup_scheduler()
    
    def load_data(self):
        """Load data from files"""
        try:
            with open('data/scheduled_posts.json', 'r') as f:
                self.scheduled_posts = json.load(f)
        except FileNotFoundError:
            self.scheduled_posts = []
        
        try:
            with open('data/posting_config.json', 'r') as f:
                saved_config = json.load(f)
                self.posting_config.update(saved_config)
        except FileNotFoundError:
            pass
        
        try:
            with open('data/bulk_titles.json', 'r') as f:
                self.bulk_titles = json.load(f)
        except FileNotFoundError:
            self.bulk_titles = []
    
    def save_data(self):
        """Save data to files"""
        with open('data/scheduled_posts.json', 'w') as f:
            json.dump(self.scheduled_posts, f, indent=2)
        with open('data/posting_config.json', 'w') as f:
            json.dump(self.posting_config, f, indent=2)
        with open('data/bulk_titles.json', 'w') as f:
            json.dump(self.bulk_titles, f, indent=2)
    
    def setup_scheduler(self):
        """Setup automatic scheduling"""
        schedule.clear()
        config = self.posting_config['posting_schedule']
        
        if config['frequency'] == 'daily':
            schedule.every().day.at(config['time']).do(self.process_scheduled_posts)
        elif config['frequency'] == 'weekly':
            for day in config['days']:
                getattr(schedule.every(), day).at(config['time']).do(self.process_scheduled_posts)
    
    def add_bulk_titles(self, titles, keywords_map=None):
        """Add multiple titles at once"""
        for title in titles:
            if title.strip():
                title_data = {
                    "title": title.strip(),
                    "keywords": keywords_map.get(title.strip(), []) if keywords_map else [],
                    "added_at": datetime.now().isoformat(),
                    "status": "pending"
                }
                self.bulk_titles.append(title_data)
        self.save_data()
        return len(titles)
    
    def process_scheduled_posts(self):
        """Process scheduled posts for today"""
        today = datetime.now().date()
        posts_to_publish = [
            p for p in self.scheduled_posts 
            if p['status'] == 'scheduled' and 
            datetime.fromisoformat(p['publish_date']).date() == today
        ]
        
        for post in posts_to_publish:
            try:
                self.publish_post(post)
            except Exception as e:
                logger.error(f"Failed to publish post {post['id']}: {str(e)}")
                post['status'] = 'failed'
                post['error'] = str(e)
        self.save_data()
    
    def publish_post(self, post):
        """Publish a single post"""
        logger.info(f"Publishing: {post['title']}")
        
        # Generate content
        article_data = generate_article(post['title'], post.get('keywords', []))
        
        # Generate image
        image_url = None
        if self.posting_config['content_settings']['auto_generate_images']:
            image_prompt = generate_image_prompt(post['title'])
            image_url = create_image(image_prompt)
        
        # Post to Blogger
        post_url = post_to_blogger(
            post['title'],
            article_data['content'],
            article_data['meta_description'],
            image_url,
            article_data['keywords']
        )
        
        # Update status
        post['status'] = 'published'
        post['published_at'] = datetime.now().isoformat()
        post['url'] = post_url
        
        logger.info(f"Published: {post_url}")

# Initialize system
auto_poster = AutoPostingSystem()

@app.route('/')
def index():
    stats = {
        "total_posts": len(auto_poster.scheduled_posts),
        "published_posts": len([p for p in auto_poster.scheduled_posts if p['status'] == 'published']),
        "scheduled_posts": len([p for p in auto_poster.scheduled_posts if p['status'] == 'scheduled']),
        "pending_titles": len([t for t in auto_poster.bulk_titles if t['status'] == 'pending'])
    }
    return render_template('index.html', 
                         posts=auto_poster.scheduled_posts[-10:],
                         bulk_titles=auto_poster.bulk_titles,
                         config=auto_poster.posting_config,
                         stats=stats)

@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        publish_date = data.get('publish_date')
        keywords = data.get('keywords', [])
        
        post_data = {
            "id": len(auto_poster.scheduled_posts) + 1,
            "title": title,
            "publish_date": publish_date,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "keywords": keywords
        }
        auto_poster.scheduled_posts.append(post_data)
        auto_poster.save_data()
        return jsonify(post_data)
    
    # GET request
    page = request.args.get('page', 1, type=int)
    per_page = 20
    start_idx = (page - 1) * per_page
    posts = auto_poster.scheduled_posts[::-1]
    return jsonify({
        "posts": posts[start_idx:start_idx + per_page],
        "total": len(posts),
        "page": page
    })

@app.route('/api/bulk-upload', methods=['POST'])
def bulk_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith('.txt'):
            content = file.read().decode('utf-8')
            titles = [line.strip() for line in content.split('\n') if line.strip()]
            df = pd.DataFrame(titles, columns=['title'])
        else:
            return jsonify({"error": "Unsupported format"}), 400
        
        titles = df.iloc[:, 0].dropna().tolist()
        count = auto_poster.add_bulk_titles(titles)
        return jsonify({"message": f"Added {count} titles", "titles": titles})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_scheduler():
    """Run scheduler in background thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scheduler thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.daemon = True
scheduler_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
