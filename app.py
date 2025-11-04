import os
import json
import schedule
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
from werkzeug.utils import secure_filename
import logging
import hashlib
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Ensure directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

class APIKeysManager:
    def __init__(self):
        self.keys_file = 'data/api_keys.json'
        self.master_key_file = 'data/master_key.hash'
        self.load_keys()
    
    def load_keys(self):
        """Load API keys from file"""
        try:
            with open(self.keys_file, 'r') as f:
                self.keys = json.load(f)
            logger.info("API keys loaded from file")
        except FileNotFoundError:
            self.keys = {
                "openai_api_key": "",
                "hf_api_key": "", 
                "blogger_blog_id": "",
                "google_client_id": "",
                "google_client_secret": "",
                "is_configured": False
            }
            self.save_keys()
    
    def save_keys(self):
        """Save API keys to file"""
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys, f, indent=2, ensure_ascii=False)
    
    def set_master_key(self, master_key):
        """Set master key for accessing the system"""
        key_hash = hashlib.sha256(master_key.encode()).hexdigest()
        with open(self.master_key_file, 'w') as f:
            f.write(key_hash)
    
    def verify_master_key(self, master_key):
        """Verify master key"""
        try:
            with open(self.master_key_file, 'r') as f:
                stored_hash = f.read().strip()
            input_hash = hashlib.sha256(master_key.encode()).hexdigest()
            return stored_hash == input_hash
        except FileNotFoundError:
            # If no master key set, allow first-time access
            return True
    
    def update_keys(self, new_keys):
        """Update API keys"""
        for key, value in new_keys.items():
            if key in self.keys and value.strip():
                self.keys[key] = value.strip()
        
        self.keys['is_configured'] = any([
            self.keys['openai_api_key'],
            self.keys['hf_api_key'], 
            self.keys['blogger_blog_id']
        ])
        
        self.save_keys()
        
        # Update environment variables for current session
        if self.keys['openai_api_key']:
            os.environ['OPENAI_API_KEY'] = self.keys['openai_api_key']
        if self.keys['hf_api_key']:
            os.environ['HF_API_KEY'] = self.keys['hf_api_key']
        if self.keys['blogger_blog_id']:
            os.environ['BLOGGER_BLOG_ID'] = self.keys['blogger_blog_id']
        
        return True
    
    def get_keys_masked(self):
        """Get masked API keys for display"""
        masked = self.keys.copy()
        for key in ['openai_api_key', 'hf_api_key', 'google_client_secret']:
            if masked[key]:
                masked[key] = masked[key][:4] + '***' + masked[key][-4:]
        return masked

# Initialize API keys manager
api_keys_manager = APIKeysManager()

# Import modules dengan fallback
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
    
    # Fallback functions
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
        return 2.0
    
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
            
            # Check if API keys are configured
            if not api_keys_manager.keys['is_configured']:
                raise Exception("API keys not configured. Please set up API keys first.")
            
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

# Authentication decorator
def require_auth(f):
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# Routes
@app.route('/')
@require_auth
def index():
    """Main dashboard"""
    try:
        stats = {
            "total_posts": len(auto_poster.scheduled_posts),
            "published_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'published']),
            "scheduled_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'scheduled']),
            "pending_titles": len([t for t in auto_poster.bulk_titles if t.get('status') == 'pending']),
            "failed_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'failed']),
            "api_configured": api_keys_manager.keys['is_configured']
        }
        
        recent_posts = auto_poster.scheduled_posts[-10:]
        recent_posts.reverse()
        
        return render_template('index.html', 
                             posts=recent_posts,
                             bulk_titles=auto_poster.bulk_titles[-20:],
                             config=auto_poster.posting_config,
                             stats=stats)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return "Error loading dashboard", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for master key authentication"""
    if request.method == 'POST':
        master_key = request.form.get('master_key')
        if api_keys_manager.verify_master_key(master_key):
            session['authenticated'] = True
            session.permanent = True
            
            # Set master key if this is first time
            if not os.path.exists(api_keys_manager.master_key_file):
                api_keys_manager.set_master_key(master_key)
                logger.info("Master key set for first time")
            
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid master key")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/settings')
@require_auth
def settings():
    """API keys settings page"""
    masked_keys = api_keys_manager.get_keys_masked()
    return render_template('settings.html', keys=masked_keys)

@app.route('/api/settings/keys', methods=['GET', 'POST'])
@require_auth
def handle_api_keys():
    """API endpoint for managing API keys"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            # Update API keys
            api_keys_manager.update_keys(data)
            
            logger.info("API keys updated via settings")
            return jsonify({
                "message": "API keys updated successfully",
                "keys": api_keys_manager.get_keys_masked()
            })
            
        except Exception as e:
            logger.error(f"Error updating API keys: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    else:  # GET request
        return jsonify({
            "keys": api_keys_manager.get_keys_masked(),
            "is_configured": api_keys_manager.keys['is_configured']
        })

@app.route('/api/settings/test', methods=['POST'])
@require_auth
def test_api_keys():
    """Test API keys connectivity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        test_results = {}
        
        # Test OpenAI API key
        if data.get('openai_api_key'):
            try:
                import openai
                openai.api_key = data['openai_api_key']
                # Simple test - list models
                models = openai.Model.list()
                test_results['openai'] = {
                    "status": "success",
                    "message": f"Connected successfully. {len(models.data)} models available."
                }
            except Exception as e:
                test_results['openai'] = {
                    "status": "error",
                    "message": str(e)
                }
        
        # Test Hugging Face API key
        if data.get('hf_api_key'):
            try:
                import requests
                headers = {"Authorization": f"Bearer {data['hf_api_key']}"}
                response = requests.get(
                    "https://huggingface.co/api/whoami",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    user_info = response.json()
                    test_results['huggingface'] = {
                        "status": "success", 
                        "message": f"Connected as {user_info.get('name', 'Unknown')}"
                    }
                else:
                    test_results['huggingface'] = {
                        "status": "error",
                        "message": f"API returned status {response.status_code}"
                    }
            except Exception as e:
                test_results['huggingface'] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return jsonify({"results": test_results})
        
    except Exception as e:
        logger.error(f"Error testing API keys: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ... (rest of the routes from previous version remain the same)

@app.route('/api/posts', methods=['GET', 'POST'])
@require_auth
def handle_posts():
    """API endpoint for posts"""
    # ... (same as previous implementation)

@app.route('/api/bulk-upload', methods=['POST'])
@require_auth
def bulk_upload():
    """Handle bulk upload of titles"""
    # ... (same as previous implementation)

@app.route('/api/schedule-bulk', methods=['POST'])
@require_auth
def schedule_bulk_titles():
    """Schedule all pending bulk titles"""
    # ... (same as previous implementation)

@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "posts_count": len(auto_poster.scheduled_posts),
        "bulk_titles_count": len(auto_poster.bulk_titles),
        "api_configured": api_keys_manager.keys['is_configured']
    })

def run_scheduler():
    """Run scheduler in background thread"""
    logger.info("Starting scheduler thread")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
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
    app.run(host='0.0.0.0', port=port, debug=debug)
