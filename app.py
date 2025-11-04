import os
import requests
import json
import schedule
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import pandas as pd
from werkzeug.utils import secure_filename
import logging

# Import modul custom
from content_generator import generate_article, research_keywords
from image_generator import generate_image_prompt, create_image
from blogger_integration import post_to_blogger, authenticate_blogger
from seo_analyzer import analyze_seo
from plagiarism_checker import check_plagiarism
from performance_tracker import track_performance

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

Session(app)

# Konfigurasi default
DEFAULT_CONFIG = {
    "posting_schedule": {
        "frequency": "daily",  # daily, weekly, monthly
        "time": "10:00",
        "days": ["monday", "wednesday", "friday"],  # untuk weekly
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

class EnhancedAutoPostingSystem:
    def __init__(self):
        self.scheduled_posts = []
        self.posting_config = DEFAULT_CONFIG.copy()
        self.bulk_titles = []
        self.load_data()
        
        # Jalankan scheduler
        self.setup_scheduler()
    
    def load_data(self):
        """Load data dari file storage"""
        try:
            with open('scheduled_posts.json', 'r') as f:
                self.scheduled_posts = json.load(f)
        except FileNotFoundError:
            self.scheduled_posts = []
        
        try:
            with open('posting_config.json', 'r') as f:
                saved_config = json.load(f)
                self.posting_config.update(saved_config)
        except FileNotFoundError:
            pass
        
        try:
            with open('bulk_titles.json', 'r') as f:
                self.bulk_titles = json.load(f)
        except FileNotFoundError:
            self.bulk_titles = []
    
    def save_data(self):
        """Simpan data ke file storage"""
        with open('scheduled_posts.json', 'w') as f:
            json.dump(self.scheduled_posts, f, indent=2)
        
        with open('posting_config.json', 'w') as f:
            json.dump(self.posting_config, f, indent=2)
        
        with open('bulk_titles.json', 'w') as f:
            json.dump(self.bulk_titles, f, indent=2)
    
    def update_config(self, new_config):
        """Update konfigurasi posting"""
        self.posting_config.update(new_config)
        self.save_data()
        self.setup_scheduler()
    
    def setup_scheduler(self):
        """Setup penjadwalan otomatis berdasarkan config"""
        schedule.clear()
        
        config = self.posting_config['posting_schedule']
        
        if config['frequency'] == 'daily':
            schedule.every().day.at(config['time']).do(
                self.process_scheduled_posts
            )
        elif config['frequency'] == 'weekly':
            for day in config['days']:
                getattr(schedule.every(), day).at(config['time']).do(
                    self.process_scheduled_posts
                )
        elif config['frequency'] == 'monthly':
            # Jadwalkan untuk tanggal 1 setiap bulan
            schedule.every().month.at(config['time']).do(
                self.process_scheduled_posts
            )
    
    def add_bulk_titles(self, titles, keywords_map=None):
        """Tambahkan banyak judul sekaligus"""
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
    
    def generate_schedule_for_bulk_titles(self):
        """Generate jadwal posting otomatis untuk semua judul yang pending"""
        config = self.posting_config['posting_schedule']
        pending_titles = [t for t in self.bulk_titles if t['status'] == 'pending']
        
        if not pending_titles:
            return 0
        
        # Hitung jadwal berdasarkan frekuensi dan max posts per day
        scheduled_count = 0
        current_date = datetime.now()
        posts_per_day = config['max_posts_per_day']
        
        for i, title_data in enumerate(pending_titles):
            if scheduled_count >= posts_per_day:
                # Pindah ke hari berikutnya
                current_date += timedelta(days=1)
                scheduled_count = 0
            
            # Set waktu posting
            post_time = datetime.strptime(config['time'], '%H:%M').time()
            publish_date = datetime.combine(current_date.date(), post_time)
            
            # Tambahkan ke scheduled posts
            post_id = len(self.scheduled_posts) + 1
            scheduled_post = {
                "id": post_id,
                "title": title_data['title'],
                "keywords": title_data['keywords'],
                "publish_date": publish_date.isoformat(),
                "status": "scheduled",
                "created_at": datetime.now().isoformat(),
                "type": "bulk"
            }
            
            self.scheduled_posts.append(scheduled_post)
            title_data['status'] = 'scheduled'
            scheduled_count += 1
        
        self.save_data()
        return len(pending_titles)
    
    def process_scheduled_posts(self):
        """Proses semua postingan yang terjadwal untuk hari ini"""
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
        """Publish sebuah post"""
        logger.info(f"Publishing post: {post['title']}")
        
        # Generate artikel
        article_data = generate_article(post['title'], post.get('keywords', []))
        
        # Generate gambar jika dienable
        image_url = None
        if self.posting_config['content_settings']['auto_generate_images']:
            image_prompt = generate_image_prompt(post['title'])
            image_url = create_image(image_prompt)
        
        # Check plagiarism jika dienable
        if self.posting_config['content_settings']['plagiarism_check']:
            plagiarism_score = check_plagiarism(article_data['content'])
            if plagiarism_score > 15:  # Threshold 15%
                raise Exception(f"Plagiarism score too high: {plagiarism_score}%")
        
        # Post ke Blogger
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
        
        # Mulai tracking performa
        track_performance(post_url, post['title'])
        
        logger.info(f"Successfully published: {post_url}")
    
    def get_stats(self):
        """Dapatkan statistik sistem"""
        total_posts = len(self.scheduled_posts)
        published_posts = len([p for p in self.scheduled_posts if p['status'] == 'published'])
        scheduled_posts = len([p for p in self.scheduled_posts if p['status'] == 'scheduled'])
        pending_titles = len([t for t in self.bulk_titles if t['status'] == 'pending'])
        
        return {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "scheduled_posts": scheduled_posts,
            "pending_titles": pending_titles,
            "success_rate": (published_posts / total_posts * 100) if total_posts > 0 else 0
        }

# Inisialisasi sistem
auto_poster = EnhancedAutoPostingSystem()

# Routes
@app.route('/')
def index():
    stats = auto_poster.get_stats()
    return render_template('index.html', 
                         posts=auto_poster.scheduled_posts[-10:],  # 10 post terakhir
                         bulk_titles=auto_poster.bulk_titles,
                         config=auto_poster.posting_config,
                         stats=stats)

@app.route('/config', methods=['GET', 'POST'])
def manage_config():
    if request.method == 'POST':
        new_config = request.json
        auto_poster.update_config(new_config)
        return jsonify({"message": "Configuration updated successfully"})
    
    return jsonify(auto_poster.posting_config)

@app.route('/bulk-upload', methods=['POST'])
def bulk_upload_titles():
    """Handle upload file CSV/Excel/TXT berisi banyak judul"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif file.filename.endswith('.txt'):
            # Baca file teks biasa
            content = file.read().decode('utf-8')
            titles = [line.strip() for line in content.split('\n') if line.strip()]
            df = pd.DataFrame(titles, columns=['title'])
        else:
            return jsonify({"error": "Unsupported file format"}), 400
        
        # Asumsikan kolom pertama adalah judul
        title_column = df.columns[0]
        titles = df[title_column].dropna().tolist()
        
        # Cek kolom keywords jika ada
        keywords_map = {}
        if 'keywords' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row[title_column]) and pd.notna(row['keywords']):
                    keywords = [k.strip() for k in str(row['keywords']).split(',')]
                    keywords_map[row[title_column]] = keywords
        
        count = auto_poster.add_bulk_titles(titles, keywords_map)
        return jsonify({"message": f"Successfully added {count} titles", "titles": titles})
    
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route('/schedule-bulk', methods=['POST'])
def schedule_bulk_titles():
    """Generate jadwal untuk semua judul yang pending"""
    try:
        count = auto_poster.generate_schedule_for_bulk_titles()
        return jsonify({"message": f"Scheduled {count} titles for posting"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add-title', methods=['POST'])
def add_single_title():
    """Tambahkan single title"""
    data = request.json
    title = data.get('title')
    keywords = data.get('keywords', [])
    publish_date = data.get('publish_date')
    
    if not title:
        return jsonify({"error": "Title is required"}), 400
    
    if publish_date:
        # Single scheduled post
        post_data = {
            "id": len(auto_poster.scheduled_posts) + 1,
            "title": title,
            "keywords": keywords,
            "publish_date": publish_date,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "type": "manual"
        }
        auto_poster.scheduled_posts.append(post_data)
    else:
        # Tambahkan ke bulk titles
        auto_poster.add_bulk_titles([title], {title: keywords} if keywords else None)
    
    auto_poster.save_data()
    return jsonify({"message": "Title added successfully"})

@app.route('/posts')
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    posts = auto_poster.scheduled_posts[::-1]  # Terbaru pertama
    paginated_posts = posts[start_idx:end_idx]
    
    return jsonify({
        "posts": paginated_posts,
        "total": len(posts),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(posts) + per_page - 1) // per_page
    })

@app.route('/bulk-titles')
def get_bulk_titles():
    status = request.args.get('status', 'all')
    if status == 'pending':
        titles = [t for t in auto_poster.bulk_titles if t['status'] == 'pending']
    elif status == 'scheduled':
        titles = [t for t in auto_poster.bulk_titles if t['status'] == 'scheduled']
    else:
        titles = auto_poster.bulk_titles
    
    return jsonify(titles)

def run_scheduler():
    """Jalankan scheduler di background thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    # Buat folder uploads jika belum ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Jalankan scheduler di thread terpisah
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
