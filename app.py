import os
import json
import schedule
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
from werkzeug.utils import secure_filename
import logging

# Configure logging for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration for Render
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Ensure directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# Import modules with fallbacks
try:
    from src.content_generator import generate_article, research_keywords
    from src.image_generator import generate_image_prompt, create_image
    from src.blogger_integration import post_to_blogger
    from src.seo_analyzer import analyze_seo
    from src.plagiarism_checker import check_plagiarism
    from src.performance_tracker import track_performance
    from src.config_manager import ConfigManager
except ImportError as e:
    logger.warning(f"Some modules not available: {e}")
    
    # Fallback functions for development
    def generate_article(title, keywords=None):
        return {
            "title": title,
            "content": f"# {title}\n\nThis is a sample article about {title}.",
            "meta_description": f"Learn about {title} in this comprehensive guide.",
            "keywords": keywords or [title],
            "word_count": 150
        }
    
    def research_keywords(title):
        return [title.lower().replace(' ', '-')]
    
    def generate_image_prompt(title):
        return f"Professional illustration about {title}"
    
    def create_image(prompt):
        return None
    
    def post_to_blogger(title, content, meta_description="", image_url="", keywords=None):
        logger.info(f"Mock posting to Blogger: {title}")
        return f"https://example.com/mock-post-{hash(title)}"
    
    def analyze_seo(content, title, keywords=None):
        return {
            "score": 85,
            "word_count": len(content.split()),
            "headings": {"h1": 1, "h2": 3, "h3": 2, "structure_score": 75},
            "readability": {"reading_level": "Good", "score": 80},
            "recommendations": ["Sample recommendation"]
        }
    
    def check_plagiarism(content):
        return 2.0  # Low plagiarism score for development
    
    def track_performance(post_url, post_title):
        logger.info(f"Tracking performance for: {post_title}")
    
    class ConfigManager:
        def __init__(self):
            self.config = {}
        def get_optimal_posting_schedule(self, num_posts):
            return [(datetime.now() + timedelta(days=i)).isoformat() for i in range(num_posts)]

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
        logger.info("AutoPostingSystem initialized")
    
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
        try:
            with open('data/scheduled_posts.json', 'w') as f:
                json.dump(self.scheduled_posts, f, indent=2)
            with open('data/posting_config.json', 'w') as f:
                json.dump(self.posting_config, f, indent=2)
            with open('data/bulk_titles.json', 'w') as f:
                json.dump(self.bulk_titles, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
    
    def setup_scheduler(self):
        """Setup automatic scheduling"""
        try:
            schedule.clear()
            config = self.posting_config['posting_schedule']
            
            if config['frequency'] == 'daily':
                schedule.every().day.at(config['time']).do(self.process_scheduled_posts)
                logger.info(f"Daily scheduler set for {config['time']}")
            elif config['frequency'] == 'weekly':
                for day in config['days']:
                    getattr(schedule.every(), day).at(config['time']).do(self.process_scheduled_posts)
                logger.info(f"Weekly scheduler set for {config['days']} at {config['time']}")
        except Exception as e:
            logger.error(f"Error setting up scheduler: {str(e)}")
    
    def add_bulk_titles(self, titles, keywords_map=None):
        """Add multiple titles at once"""
        added_count = 0
        for title in titles:
            if title and title.strip():
                title_data = {
                    "title": title.strip(),
                    "keywords": keywords_map.get(title.strip(), []) if keywords_map else [],
                    "added_at": datetime.now().isoformat(),
                    "status": "pending"
                }
                self.bulk_titles.append(title_data)
                added_count += 1
        
        self.save_data()
        logger.info(f"Added {added_count} bulk titles")
        return added_count
    
    def process_scheduled_posts(self):
        """Process scheduled posts for today"""
        try:
            today = datetime.now().date()
            posts_to_publish = [
                p for p in self.scheduled_posts 
                if p.get('status') == 'scheduled' and 
                datetime.fromisoformat(p['publish_date']).date() == today
            ]
            
            logger.info(f"Processing {len(posts_to_publish)} scheduled posts for today")
            
            for post in posts_to_publish:
                try:
                    self.publish_post(post)
                except Exception as e:
                    logger.error(f"Failed to publish post {post.get('id')}: {str(e)}")
                    post['status'] = 'failed'
                    post['error'] = str(e)
            
            self.save_data()
        except Exception as e:
            logger.error(f"Error processing scheduled posts: {str(e)}")
    
    def publish_post(self, post):
        """Publish a single post"""
        try:
            logger.info(f"Publishing post: {post['title']}")
            
            # Generate article content
            article_data = generate_article(post['title'], post.get('keywords', []))
            
            # Generate image if enabled
            image_url = None
            if self.posting_config['content_settings']['auto_generate_images']:
                image_prompt = generate_image_prompt(post['title'])
                image_url = create_image(image_prompt)
                if image_url:
                    logger.info(f"Generated image: {image_url}")
            
            # Check plagiarism if enabled
            if self.posting_config['content_settings']['plagiarism_check']:
                plagiarism_score = check_plagiarism(article_data['content'])
                if plagiarism_score > 15:  # Threshold 15%
                    raise Exception(f"Plagiarism score too high: {plagiarism_score}%")
            
            # Post to Blogger
            post_url = post_to_blogger(
                post['title'],
                article_data['content'],
                article_data['meta_description'],
                image_url,
                article_data['keywords']
            )
            
            # Update post status
            post['status'] = 'published'
            post['published_at'] = datetime.now().isoformat()
            post['url'] = post_url
            post['word_count'] = article_data['word_count']
            
            # Start performance tracking
            track_performance(post_url, post['title'])
            
            logger.info(f"Successfully published: {post_url}")
            
        except Exception as e:
            logger.error(f"Error publishing post: {str(e)}")
            raise

# Initialize system
auto_poster = AutoPostingSystem()

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    try:
        stats = {
            "total_posts": len(auto_poster.scheduled_posts),
            "published_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'published']),
            "scheduled_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'scheduled']),
            "pending_titles": len([t for t in auto_poster.bulk_titles if t.get('status') == 'pending']),
            "failed_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'failed'])
        }
        
        recent_posts = auto_poster.scheduled_posts[-10:]  # Last 10 posts
        recent_posts.reverse()  # Show newest first
        
        return render_template('index.html', 
                             posts=recent_posts,
                             bulk_titles=auto_poster.bulk_titles[-20:],  # Last 20 titles
                             config=auto_poster.posting_config,
                             stats=stats)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return "Error loading dashboard", 500

@app.route('/api/posts', methods=['GET', 'POST'])
def handle_posts():
    """API endpoint for posts"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            title = data.get('title')
            publish_date = data.get('publish_date')
            keywords = data.get('keywords', [])
            
            if not title:
                return jsonify({"error": "Title is required"}), 400
            
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
            
            logger.info(f"Created new post: {title}")
            return jsonify(post_data)
            
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    else:  # GET request
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            start_idx = (page - 1) * per_page
            
            # Reverse to show newest first
            posts = auto_poster.scheduled_posts[::-1]
            total_posts = len(posts)
            
            paginated_posts = posts[start_idx:start_idx + per_page]
            
            return jsonify({
                "posts": paginated_posts,
                "total": total_posts,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_posts + per_page - 1) // per_page
            })
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/bulk-upload', methods=['POST'])
def bulk_upload():
    """Handle bulk upload of titles"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Process different file types
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif file.filename.endswith('.txt'):
            content = file.read().decode('utf-8')
            titles = [line.strip() for line in content.split('\n') if line.strip()]
            df = pd.DataFrame(titles, columns=['title'])
        else:
            return jsonify({"error": "Unsupported file format. Use CSV, Excel, or TXT"}), 400
        
        # Extract titles and keywords
        title_column = df.columns[0]  # First column is titles
        titles = df[title_column].dropna().tolist()
        
        keywords_map = {}
        if 'keywords' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row[title_column]) and pd.notna(row['keywords']):
                    keywords = [k.strip() for k in str(row['keywords']).split(',')]
                    keywords_map[row[title_column]] = keywords
        
        count = auto_poster.add_bulk_titles(titles, keywords_map)
        
        logger.info(f"Bulk upload processed: {count} titles")
        return jsonify({
            "message": f"Successfully added {count} titles",
            "titles": titles,
            "count": count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route('/api/schedule-bulk', methods=['POST'])
def schedule_bulk_titles():
    """Schedule all pending bulk titles"""
    try:
        pending_titles = [t for t in auto_poster.bulk_titles if t.get('status') == 'pending']
        
        if not pending_titles:
            return jsonify({"message": "No pending titles to schedule"})
        
        config = auto_poster.posting_config['posting_schedule']
        posts_per_day = config.get('max_posts_per_day', 2)
        
        scheduled_count = 0
        current_date = datetime.now()
        
        for title_data in pending_titles:
            if scheduled_count >= posts_per_day:
                current_date += timedelta(days=1)
                scheduled_count = 0
            
            post_time = datetime.strptime(config['time'], '%H:%M').time()
            publish_date = datetime.combine(current_date.date(), post_time)
            
            post_id = len(auto_poster.scheduled_posts) + 1
            scheduled_post = {
                "id": post_id,
                "title": title_data['title'],
                "keywords": title_data['keywords'],
                "publish_date": publish_date.isoformat(),
                "status": "scheduled",
                "created_at": datetime.now().isoformat(),
                "type": "bulk"
            }
            
            auto_poster.scheduled_posts.append(scheduled_post)
            title_data['status'] = 'scheduled'
            scheduled_count += 1
        
        auto_poster.save_data()
        
        logger.info(f"Scheduled {len(pending_titles)} bulk titles")
        return jsonify({
            "message": f"Scheduled {len(pending_titles)} titles",
            "scheduled_count": len(pending_titles)
        })
        
    except Exception as e:
        logger.error(f"Error scheduling bulk titles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "posts_count": len(auto_poster.scheduled_posts),
        "bulk_titles_count": len(auto_poster.bulk_titles)
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

def run_scheduler():
    """Run scheduler in background thread"""
    logger.info("Starting scheduler thread")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            time.sleep(60)

# Start scheduler thread when not in development
if os.getenv('FLASK_ENV') != 'development':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    if debug:
        # Development server
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        # Production server
        app.run(host='0.0.0.0', port=port, debug=debug)
