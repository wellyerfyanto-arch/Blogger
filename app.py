import os
import json
import csv
import schedule
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import logging
import hashlib
import secrets
import atexit

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
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Ensure directories exist
os.makedirs('data', exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/samples', exist_ok=True)

# Global variable untuk kontrol scheduler
scheduler_running = True
scheduler_thread = None

# ... (APIKeysManager, fallback functions, AutoPostingSystem classes tetap sama)
# HANYA bagian yang berkaitan dengan scheduler yang diupdate

class AutoPostingSystem:
    def __init__(self):
        self.scheduled_posts = []
        self.posting_config = DEFAULT_CONFIG.copy()
        self.bulk_titles = []
        self.load_data()
        self.setup_scheduler()
        logger.info("AutoPostingSystem initialized")
    
    def setup_scheduler(self):
        """Setup automatic scheduling dengan improved error handling"""
        try:
            schedule.clear()
            config = self.posting_config['posting_schedule']
            
            # Convert time to UTC jika perlu
            posting_time = config['time']
            
            if config['frequency'] == 'daily':
                schedule.every().day.at(posting_time).do(self.process_scheduled_posts)
                logger.info(f"✅ Daily scheduler set for {posting_time} UTC")
            elif config['frequency'] == 'weekly':
                for day in config['days']:
                    getattr(schedule.every(), day).at(posting_time).do(self.process_scheduled_posts)
                logger.info(f"✅ Weekly scheduler set for {config['days']} at {posting_time} UTC")
            elif config['frequency'] == 'hourly':
                schedule.every().hour.do(self.process_scheduled_posts)
                logger.info("✅ Hourly scheduler set")
                
        except Exception as e:
            logger.error(f"❌ Error setting up scheduler: {str(e)}")
    
    def process_scheduled_posts(self):
        """Process scheduled posts for today dengan improved logging"""
        try:
            now = datetime.now()
            logger.info(f"🕒 Running scheduled post check at {now}")
            
            # Cek posts yang seharusnya dipublish hari ini
            today = now.date()
            posts_to_publish = [
                p for p in self.scheduled_posts 
                if p.get('status') == 'scheduled' and 
                datetime.fromisoformat(p['publish_date']).date() <= today
            ]
            
            logger.info(f"📋 Found {len(posts_to_publish)} posts to publish today")
            
            if not posts_to_publish:
                logger.info("ℹ️ No posts to publish today")
                return
            
            published_count = 0
            for post in posts_to_publish:
                try:
                    logger.info(f"🚀 Attempting to publish: {post['title']}")
                    self.publish_post(post)
                    published_count += 1
                    logger.info(f"✅ Successfully published: {post['title']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to publish post {post.get('id')}: {str(e)}")
                    post['status'] = 'failed'
                    post['error'] = str(e)
                    post['last_attempt'] = now.isoformat()
            
            self.save_data()
            logger.info(f"🎉 Scheduled posts processing completed. Published: {published_count}, Failed: {len(posts_to_publish) - published_count}")
            
        except Exception as e:
            logger.error(f"💥 Critical error in process_scheduled_posts: {str(e)}", exc_info=True)

    def publish_post(self, post):
        """Publish a single post dengan improved error handling"""
        try:
            logger.info(f"📝 Starting publication for: {post['title']}")
            
            if not api_keys_manager.keys.get('is_configured'):
                raise Exception("API keys not configured. Please set up API keys first.")
            
            # Generate article content
            logger.info("🤖 Generating article content...")
            article_data = generate_article(post['title'], post.get('keywords', []))
            
            # Generate image if enabled
            image_url = None
            if self.posting_config['content_settings']['auto_generate_images']:
                logger.info("🎨 Generating image...")
                image_prompt = generate_image_prompt(post['title'])
                image_url = create_image(image_prompt)
                if image_url:
                    logger.info(f"🖼️ Image generated: {image_url}")
                else:
                    logger.warning("⚠️ Image generation failed or skipped")
            
            # Check plagiarism if enabled
            if self.posting_config['content_settings']['plagiarism_check']:
                logger.info("🔍 Checking plagiarism...")
                plagiarism_score = check_plagiarism(article_data['content'])
                if plagiarism_score > 15:
                    raise Exception(f"Plagiarism score too high: {plagiarism_score}%")
            
            # Post to Blogger
            logger.info("📤 Posting to Blogger...")
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
            
            logger.info(f"✅ Successfully published: {post_url}")
            
        except Exception as e:
            logger.error(f"❌ Error publishing post: {str(e)}")
            raise

# Initialize system
auto_poster = AutoPostingSystem()

# Scheduler Functions
def run_scheduler():
    """Run scheduler in background thread dengan improved reliability"""
    logger.info("🚀 Starting scheduler thread...")
    
    # Initial check on startup
    logger.info("🔍 Running initial post check...")
    try:
        auto_poster.process_scheduled_posts()
    except Exception as e:
        logger.error(f"❌ Initial post check failed: {str(e)}")
    
    # Main scheduler loop
    while scheduler_running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Log heartbeat every 10 minutes
            if int(time.time()) % 600 == 0:
                logger.info("💓 Scheduler heartbeat - running normally")
                
        except Exception as e:
            logger.error(f"💥 Scheduler loop error: {str(e)}")
            time.sleep(60)  # Wait before retrying
    
    logger.info("🛑 Scheduler thread stopped")

def start_scheduler():
    """Start the scheduler thread"""
    global scheduler_thread, scheduler_running
    
    if scheduler_thread and scheduler_thread.is_alive():
        logger.info("✅ Scheduler already running")
        return
    
    scheduler_running = True
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("✅ Scheduler thread started successfully")

def stop_scheduler():
    """Stop the scheduler thread"""
    global scheduler_running
    scheduler_running = False
    logger.info("🛑 Scheduler stop requested")

# Register cleanup function
atexit.register(stop_scheduler)

# ... (Routes tetap sama, TAMBAHKAN routes baru untuk scheduler control)

@app.route('/api/scheduler/status')
@require_auth
def get_scheduler_status():
    """Get scheduler status"""
    status = {
        "scheduler_running": scheduler_running,
        "scheduler_thread_alive": scheduler_thread.is_alive() if scheduler_thread else False,
        "next_run": str(schedule.next_run()) if schedule.jobs else "No jobs scheduled",
        "scheduled_jobs": len(schedule.jobs),
        "current_time": datetime.now().isoformat()
    }
    return jsonify(status)

@app.route('/api/scheduler/trigger', methods=['POST'])
@require_auth
def trigger_scheduler_manual():
    """Trigger scheduler manually untuk testing"""
    try:
        logger.info("🔧 Manual scheduler trigger requested")
        auto_poster.process_scheduled_posts()
        return jsonify({
            "success": True,
            "message": "Scheduler triggered manually"
        })
    except Exception as e:
        logger.error(f"❌ Manual trigger failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/scheduler/restart', methods=['POST'])
@require_auth
def restart_scheduler():
    """Restart scheduler"""
    try:
        stop_scheduler()
        time.sleep(2)
        start_scheduler()
        
        return jsonify({
            "success": True,
            "message": "Scheduler restarted successfully"
        })
    except Exception as e:
        logger.error(f"❌ Scheduler restart failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/posts/check-queue')
@require_auth
def check_post_queue():
    """Check posts that are ready to be published"""
    try:
        now = datetime.now()
        today = now.date()
        
        scheduled_posts = [
            p for p in auto_poster.scheduled_posts 
            if p.get('status') == 'scheduled'
        ]
        
        posts_due = [
            p for p in scheduled_posts 
            if datetime.fromisoformat(p['publish_date']).date() <= today
        ]
        
        upcoming_posts = [
            p for p in scheduled_posts 
            if datetime.fromisoformat(p['publish_date']).date() > today
        ]
        
        return jsonify({
            "current_time": now.isoformat(),
            "scheduled_posts_count": len(scheduled_posts),
            "posts_due_count": len(posts_due),
            "upcoming_posts_count": len(upcoming_posts),
            "posts_due": [{
                "id": p["id"],
                "title": p["title"],
                "scheduled_date": p["publish_date"],
                "days_until": (datetime.fromisoformat(p['publish_date']).date() - today).days
            } for p in posts_due],
            "upcoming_posts": [{
                "id": p["id"],
                "title": p["title"], 
                "scheduled_date": p["publish_date"],
                "days_until": (datetime.fromisoformat(p['publish_date']).date() - today).days
            } for p in upcoming_posts]
        })
        
    except Exception as e:
        logger.error(f"Error checking post queue: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ... (Routes lainnya tetap sama)

# Start scheduler when app starts
@app.before_first_request
def startup():
    """Start scheduler when app starts"""
    logger.info("🚀 Application starting up...")
    start_scheduler()

# Update main block
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Print debug info on startup
    logger.info(f"🚀 Starting app on port {port}, debug: {debug}")
    logger.info(f"📁 Data directory exists: {os.path.exists('data')}")
    
    # Start scheduler
    start_scheduler()
    
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)d data from files dengan error handling"""
        try:
            # Load scheduled posts
            if os.path.exists('data/scheduled_posts.json'):
                with open('data/scheduled_posts.json', 'r') as f:
                    content = f.read().strip()
                    self.scheduled_posts = json.loads(content) if content else []
            else:
                self.scheduled_posts = []
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error loading scheduled posts: {str(e)}")
            self.scheduled_posts = []
        
        try:
            # Load posting config
            if os.path.exists('data/posting_config.json'):
                with open('data/posting_config.json', 'r') as f:
                    content = f.read().strip()
                    if content:
                        saved_config = json.loads(content)
                        self.posting_config.update(saved_config)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error loading posting config: {str(e)}")
        
        try:
            # Load bulk titles
            if os.path.exists('data/bulk_titles.json'):
                with open('data/bulk_titles.json', 'r') as f:
                    content = f.read().strip()
                    self.bulk_titles = json.loads(content) if content else []
            else:
                self.bulk_titles = []
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error loading bulk titles: {str(e)}")
            self.bulk_titles = []
    
    def save_data(self):
        """Save data to files dengan error handling"""
        try:
            with open('data/scheduled_posts.json', 'w') as f:
                json.dump(self.scheduled_posts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving scheduled posts: {str(e)}")
        
        try:
            with open('data/posting_config.json', 'w') as f:
                json.dump(self.posting_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving posting config: {str(e)}")
        
        try:
            with open('data/bulk_titles.json', 'w') as f:
                json.dump(self.bulk_titles, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving bulk titles: {str(e)}")
    
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
    
    def run_scheduler():
    """Run scheduler in background thread dengan improved reliability"""
    logger.info("🚀 Starting scheduler thread...")
    
    # Initial check on startup
    logger.info("🔍 Running initial post check...")
    try:
        auto_poster.process_scheduled_posts()
    except Exception as e:
        logger.error(f"❌ Initial post check failed: {str(e)}")
    
    # Main scheduler loop
    while scheduler_running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Log heartbeat every 10 minutes
            if int(time.time()) % 600 == 0:
                logger.info("💓 Scheduler heartbeat - running normally")
                
        except Exception as e:
            logger.error(f"💥 Scheduler loop error: {str(e)}")
            time.sleep(60)  # Wait before retrying
    
    logger.info("🛑 Scheduler thread stopped")

def start_scheduler():
    """Start the scheduler thread"""
    global scheduler_thread, scheduler_running
    
    if scheduler_thread and scheduler_thread.is_alive():
        logger.info("✅ Scheduler already running")
        return
    
    scheduler_running = True
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("✅ Scheduler thread started successfully")

def stop_scheduler():
    """Stop the scheduler thread"""
    global scheduler_running
    scheduler_running = False
    logger.info("🛑 Scheduler stop requested")

# Register cleanup function
atexit.register(stop_scheduler)

# ... (Routes tetap sama, TAMBAHKAN routes baru untuk scheduler control)

@app.route('/api/scheduler/status')
@require_auth
def get_scheduler_status():
    """Get scheduler status"""
    status = {
        "scheduler_running": scheduler_running,
        "scheduler_thread_alive": scheduler_thread.is_alive() if scheduler_thread else False,
        "next_run": str(schedule.next_run()) if schedule.jobs else "No jobs scheduled",
        "scheduled_jobs": len(schedule.jobs),
        "current_time": datetime.now().isoformat()
    }
    return jsonify(status)

@app.route('/api/scheduler/trigger', methods=['POST'])
@require_auth
def trigger_scheduler_manual():
    """Trigger scheduler manually untuk testing"""
    try:
        logger.info("🔧 Manual scheduler trigger requested")
        auto_poster.process_scheduled_posts()
        return jsonify({
            "success": True,
            "message": "Scheduler triggered manually"
        })
    except Exception as e:
        logger.error(f"❌ Manual trigger failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/scheduler/restart', methods=['POST'])
@require_auth
def restart_scheduler():
    """Restart scheduler"""
    try:
        stop_scheduler()
        time.sleep(2)
        start_scheduler()
        
        return jsonify({
            "success": True,
            "message": "Scheduler restarted successfully"
        })
    except Exception as e:
        logger.error(f"❌ Scheduler restart failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/posts/check-queue')
@require_auth
def check_post_queue():
    """Check posts that are ready to be published"""
    try:
        now = datetime.now()
        today = now.date()
        
        scheduled_posts = [
            p for p in auto_poster.scheduled_posts 
            if p.get('status') == 'scheduled'
        ]
        
        posts_due = [
            p for p in scheduled_posts 
            if datetime.fromisoformat(p['publish_date']).date() <= today
        ]
        
        upcoming_posts = [
            p for p in scheduled_posts 
            if datetime.fromisoformat(p['publish_date']).date() > today
        ]
        
        return jsonify({
            "current_time": now.isoformat(),
            "scheduled_posts_count": len(scheduled_posts),
            "posts_due_count": len(posts_due),
            "upcoming_posts_count": len(upcoming_posts),
            "posts_due": [{
                "id": p["id"],
                "title": p["title"],
                "scheduled_date": p["publish_date"],
                "days_until": (datetime.fromisoformat(p['publish_date']).date() - today).days
            } for p in posts_due],
            "upcoming_posts": [{
                "id": p["id"],
                "title": p["title"], 
                "scheduled_date": p["publish_date"],
                "days_until": (datetime.fromisoformat(p['publish_date']).date() - today).days
            } for p in upcoming_posts]
        })
        
    except Exception as e:
        logger.error(f"Error checking post queue: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ... (Routes lainnya tetap sama)

# Start scheduler when app starts
@app.before_first_request
def startup():
    """Start scheduler when app starts"""
    logger.info("🚀 Application starting up...")
    start_scheduler()

# Update main block
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Print debug info on startup
    logger.info(f"🚀 Starting app on port {port}, debug: {debug}")
    logger.info(f"📁 Data directory exists: {os.path.exists('data')}")
    
    # Start scheduler
    start_scheduler()
    
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
    
    def publish_post(self, post):
        """Publish a single post"""
        try:
            logger.info(f"Publishing post: {post['title']}")
            
            if not api_keys_manager.keys.get('is_configured'):
                raise Exception("API keys not configured. Please set up API keys first.")
            
            article_data = generate_article(post['title'], post.get('keywords', []))
            
            image_url = None
            if self.posting_config['content_settings']['auto_generate_images']:
                image_prompt = generate_image_prompt(post['title'])
                image_url = create_image(image_prompt)
                if image_url:
                    logger.info(f"Generated image: {image_url}")
            
            if self.posting_config['content_settings']['plagiarism_check']:
                plagiarism_score = check_plagiarism(article_data['content'])
                if plagiarism_score > 15:
                    raise Exception(f"Plagiarism score too high: {plagiarism_score}%")
            
            post_url = post_to_blogger(
                post['title'],
                article_data['content'],
                article_data['meta_description'],
                image_url,
                article_data['keywords']
            )
            
            post['status'] = 'published'
            post['published_at'] = datetime.now().isoformat()
            post['url'] = post_url
            post['word_count'] = article_data['word_count']
            
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

# Utility functions for file processing
def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed_extensions = {'csv', 'txt'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def detect_delimiter(first_line):
    """Detect CSV delimiter from first line"""
    delimiters = [',', ';', '\t', '|']
    max_count = 0
    best_delimiter = ','
    
    for delimiter in delimiters:
        count = first_line.count(delimiter)
        if count > max_count:
            max_count = count
            best_delimiter = delimiter
    
    return best_delimiter

def process_csv_file(file):
    """Process CSV file dengan improved error handling"""
    titles = []
    keywords_map = {}
    
    try:
        # Reset file pointer
        file.stream.seek(0)
        
        # Try different encodings
        content = None
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                file.stream.seek(0)
                content = file.stream.read().decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            logger.error("Could not decode file with any encoding")
            return titles, keywords_map
        
        # Split into lines and process
        lines = content.splitlines()
        logger.info(f"CSV file has {len(lines)} lines")
        
        if not lines:
            return titles, keywords_map
        
        # Detect delimiter
        first_line = lines[0]
        delimiter = detect_delimiter(first_line)
        logger.info(f"Detected delimiter: {repr(delimiter)}")
        
        # Process CSV
        reader = csv.reader(lines, delimiter=delimiter)
        
        # Get headers
        try:
            headers = next(reader)
            logger.info(f"CSV headers: {headers}")
        except StopIteration:
            logger.error("CSV file is empty")
            return titles, keywords_map
        
        # Determine column indices
        title_index = 0  # Default to first column
        keyword_index = None
        
        # Try to find title and keyword columns
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            if any(keyword in header_lower for keyword in ['title', 'judul', 'post', 'article']):
                title_index = i
                logger.info(f"Title column found at index {i}: {header}")
            elif 'keyword' in header_lower:
                keyword_index = i
                logger.info(f"Keyword column found at index {i}: {header}")
        
        # Process rows
        for row_num, row in enumerate(reader, start=2):
            try:
                if not row:  # Skip empty rows
                    continue
                
                # Get title
                if len(row) > title_index:
                    title = row[title_index].strip()
                    if title:  # Only process non-empty titles
                        titles.append(title)
                        
                        # Get keywords if available
                        if keyword_index is not None and len(row) > keyword_index:
                            keyword_str = row[keyword_index].strip()
                            if keyword_str:
                                keywords = [k.strip() for k in keyword_str.split(',') if k.strip()]
                                keywords_map[title] = keywords
                                logger.debug(f"Row {row_num}: Title='{title}', Keywords={keywords}")
                            else:
                                logger.debug(f"Row {row_num}: Title='{title}', No keywords")
                        else:
                            logger.debug(f"Row {row_num}: Title='{title}'")
                    else:
                        logger.warning(f"Row {row_num}: Empty title, skipping")
                else:
                    logger.warning(f"Row {row_num}: No title column found")
                    
            except Exception as e:
                logger.warning(f"Error processing row {row_num}: {str(e)}")
                continue
        
        logger.info(f"CSV processing completed: {len(titles)} valid titles found")
        return titles, keywords_map
        
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}", exc_info=True)
        return titles, keywords_map

def process_txt_file(file):
    """Process TXT file dengan improved error handling"""
    titles = []
    
    try:
        # Reset file pointer
        file.stream.seek(0)
        
        # Try different encodings
        content = None
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                file.stream.seek(0)
                content = file.stream.read().decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            logger.error("Could not decode TXT file with any encoding")
            return titles, {}
        
        # Process each line
        lines = content.split('\n')
        logger.info(f"TXT file has {len(lines)} lines")
        
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                titles.append(line)
                logger.debug(f"Line {line_num}: '{line}'")
        
        logger.info(f"TXT processing completed: {len(titles)} valid titles found")
        return titles, {}
        
    except Exception as e:
        logger.error(f"Error processing TXT file: {str(e)}", exc_info=True)
        return titles, {}

# Routes
@app.route('/')
def index():
    """Main dashboard dengan improved error handling"""
    try:
        # Check if user is authenticated
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        
        # Get stats dengan safe access
        stats = {
            "total_posts": len(auto_poster.scheduled_posts),
            "published_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'published']),
            "scheduled_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'scheduled']),
            "pending_titles": len([t for t in auto_poster.bulk_titles if t.get('status') == 'pending']),
            "failed_posts": len([p for p in auto_poster.scheduled_posts if p.get('status') == 'failed']),
            "api_configured": api_keys_manager.keys.get('is_configured', False)
        }
        
        # Get recent posts safely
        recent_posts = auto_poster.scheduled_posts[-10:] if auto_poster.scheduled_posts else []
        recent_posts.reverse()
        
        # Get bulk titles safely
        bulk_titles_display = auto_poster.bulk_titles[-20:] if auto_poster.bulk_titles else []
        
        return render_template('index.html', 
                             posts=recent_posts,
                             bulk_titles=bulk_titles_display,
                             config=auto_poster.posting_config,
                             stats=stats)
                             
    except Exception as e:
        logger.error(f"Critical error in index route: {str(e)}")
        return """
        <html>
            <head><title>Error</title></head>
            <body>
                <h2>System Error</h2>
                <p>There was an error loading the dashboard. Please try logging in again.</p>
                <p><a href="/login">Go to Login</a></p>
                <details>
                    <summary>Technical Details</summary>
                    <pre>{}</pre>
                </details>
            </body>
        </html>
        """.format(str(e)), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page dengan improved error handling"""
    try:
        if request.method == 'POST':
            master_key = request.form.get('master_key', '').strip()
            
            if not master_key:
                return render_template('login.html', error="Please enter a master key")
            
            if api_keys_manager.verify_master_key(master_key):
                session['authenticated'] = True
                session.permanent = True
                
                # Set master key if this is first time
                if not os.path.exists(api_keys_manager.master_key_file):
                    api_keys_manager.set_master_key(master_key)
                    logger.info("Master key set for first time")
                
                logger.info("User logged in successfully")
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Invalid master key")
        
        return render_template('login.html')
        
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return render_template('login.html', error=f"System error: {str(e)}")

@app.route('/logout')
def logout():
    """Logout user"""
    try:
        session.pop('authenticated', None)
        logger.info("User logged out")
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return redirect(url_for('login'))

@app.route('/settings')
@require_auth
def settings():
    """API keys settings page"""
    try:
        masked_keys = api_keys_manager.get_keys_masked()
        return render_template('settings.html', keys=masked_keys)
    except Exception as e:
        logger.error(f"Error in settings route: {str(e)}")
        return "Error loading settings", 500

@app.route('/api/settings/keys', methods=['GET', 'POST'])
@require_auth
def handle_api_keys():
    """API endpoint for managing API keys"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            success = api_keys_manager.update_keys(data)
            
            if success:
                return jsonify({
                    "message": "API keys updated successfully",
                    "keys": api_keys_manager.get_keys_masked()
                })
            else:
                return jsonify({"error": "Failed to update API keys"}), 500
        
        else:  # GET request
            return jsonify({
                "keys": api_keys_manager.get_keys_masked(),
                "is_configured": api_keys_manager.keys.get('is_configured', False)
            })
            
    except Exception as e:
        logger.error(f"Error in handle_api_keys: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

@app.route('/api/posts', methods=['GET', 'POST'])
@require_auth
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
    
    else:
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 20
            start_idx = (page - 1) * per_page
            
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
@require_auth
def bulk_upload():
    """Handle bulk upload of titles dengan improved error handling"""
    try:
        # Check if file is provided
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            logger.error("No file selected")
            return jsonify({"error": "No file selected"}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            logger.error(f"File type not allowed: {file.filename}")
            return jsonify({"error": "File type not allowed. Please upload CSV or TXT file"}), 400
        
        logger.info(f"Processing uploaded file: {file.filename}")
        
        titles = []
        keywords_map = {}
        
        # Process based on file type
        if file.filename.lower().endswith('.csv'):
            titles, keywords_map = process_csv_file(file)
            logger.info(f"CSV processing completed: {len(titles)} titles found")
            
        elif file.filename.lower().endswith('.txt'):
            titles, keywords_map = process_txt_file(file)
            logger.info(f"TXT processing completed: {len(titles)} titles found")
        
        else:
            return jsonify({"error": "Unsupported file format. Use CSV or TXT"}), 400
        
        # Validate that we got some titles
        if not titles:
            logger.warning("No valid titles found in uploaded file")
            return jsonify({"error": "No valid titles found in the file. Please check the file format."}), 400
        
        # Add titles to system
        count = auto_poster.add_bulk_titles(titles, keywords_map)
        
        logger.info(f"Bulk upload successful: {count} titles added")
        return jsonify({
            "success": True,
            "message": f"Successfully added {count} titles",
            "titles": titles[:10],  # Return first 10 titles for preview
            "count": count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route('/api/schedule-bulk', methods=['POST'])
@require_auth
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

@app.route('/api/bulk-titles')
@require_auth
def get_bulk_titles():
    """Get all bulk titles"""
    try:
        return jsonify(auto_poster.bulk_titles)
    except Exception as e:
        logger.error(f"Error getting bulk titles: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "posts_count": len(auto_poster.scheduled_posts),
            "bulk_titles_count": len(auto_poster.bulk_titles),
            "api_configured": api_keys_manager.keys.get('is_configured', False),
            "authenticated": session.get('authenticated', False)
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/debug')
def debug_info():
    """Debug endpoint untuk troubleshooting"""
    debug_info = {
        "session_authenticated": session.get('authenticated', False),
        "master_key_exists": os.path.exists(api_keys_manager.master_key_file),
        "data_files_exist": {
            "scheduled_posts": os.path.exists('data/scheduled_posts.json'),
            "posting_config": os.path.exists('data/posting_config.json'),
            "bulk_titles": os.path.exists('data/bulk_titles.json'),
            "api_keys": os.path.exists('data/api_keys.json')
        },
        "scheduled_posts_count": len(auto_poster.scheduled_posts),
        "bulk_titles_count": len(auto_poster.bulk_titles),
        "api_configured": api_keys_manager.keys.get('is_configured', False)
    }
    return jsonify(debug_info)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/static/samples/<filename>')
def serve_sample_file(filename):
    """Serve sample files untuk download"""
    try:
        return send_from_directory('static/samples', filename)
    except FileNotFoundError:
        return "File not found", 404

@app.route('/api/debug/upload-test', methods=['POST'])
@require_auth
def debug_upload_test():
    """Debug endpoint untuk test upload functionality"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        debug_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "content_length": len(file.read()) if file else 0,
            "headers": dict(request.headers)
        }
        
        # Reset file pointer for processing
        file.seek(0)
        
        # Test processing
        if file.filename.endswith('.csv'):
            titles, keywords = process_csv_file(file)
            debug_info["processing_result"] = {
                "titles_found": len(titles),
                "keywords_found": len(keywords),
                "sample_titles": titles[:3],
                "sample_keywords": dict(list(keywords.items())[:3])
            }
        elif file.filename.endswith('.txt'):
            titles, keywords = process_txt_file(file)
            debug_info["processing_result"] = {
                "titles_found": len(titles),
                "sample_titles": titles[:3]
            }
        
        return jsonify(debug_info)
        
    except Exception as e:
        logger.error(f"Debug upload test error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def create_sample_files():
    """Create sample files if they don't exist"""
    samples_dir = 'static/samples'
    os.makedirs(samples_dir, exist_ok=True)
    
    # Create sample CSV
    sample_csv = """title,keywords
Cara Investasi Bitcoin untuk Pemula 2024,bitcoin,investasi,pemula,crypto,2024
Panduan Lengkap Trading Crypto,trading,crypto,panduan,strategi,binance
Review Exchange Binance: Kelebihan dan Kekurangan,binance,exchange,review,keamanan,trading
Mengenal Blockchain Technology dari Dasar,blockchain,teknologi,dasar,pemula,crypto
Strategi Portfolio Crypto yang Menguntungkan,portfolio,strategi,investasi,crypto,profit
Cara Aman Menyimpan Crypto di Wallet,wallet,keamanan,penyimpanan,crypto,private key
Analisis Market Bitcoin: Prediksi Harga 2024,bitcoin,analisis,prediksi,harga,market
10 Altcoin Potensial dengan ROI Tinggi,altcoin,potensial,roi,investasi,crypto
Panduan Mining Ethereum untuk Pemula,mining,ethereum,pemula,hardware,profit
NFT untuk Pemula: Panduan Lengkap Investasi,nft,pemula,investasi,digital asset,marketplace"""
    
    with open(os.path.join(samples_dir, 'sample_titles.csv'), 'w', encoding='utf-8') as f:
        f.write(sample_csv)
    
    # Create sample TXT
    sample_txt = """Cara Investasi Bitcoin untuk Pemula 2024
Panduan Lengkap Trading Crypto
Review Exchange Binance: Kelebihan dan Kekurangan
Mengenal Blockchain Technology dari Dasar
Strategi Portfolio Crypto yang Menguntungkan
Cara Aman Menyimpan Crypto di Wallet
Analisis Market Bitcoin: Prediksi Harga 2024
10 Altcoin Potensial dengan ROI Tinggi
Panduan Mining Ethereum untuk Pemula
NFT untuk Pemula: Panduan Lengkap Investasi"""
    
    with open(os.path.join(samples_dir, 'sample_titles.txt'), 'w', encoding='utf-8') as f:
        f.write(sample_txt)
    
    logger.info("Sample files created successfully")

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

# Initialize sample files and start scheduler
create_sample_files()

# Start scheduler thread when not in development
if os.getenv('FLASK_ENV') != 'development':
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler thread started")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    # Print debug info on startup
    logger.info(f"Starting app on port {port}, debug: {debug}")
    logger.info(f"Data directory exists: {os.path.exists('data')}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
