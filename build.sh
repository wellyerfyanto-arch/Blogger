#!/bin/bash
set -e  # Exit on error

echo "🚀 Starting build process on Render..."

# Upgrade pip first
python -m pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data uploads static/images templates

# Create initial data files with proper content
echo "📊 Initializing data files..."

# Initialize scheduled_posts.json
if [ ! -f "data/scheduled_posts.json" ] || [ ! -s "data/scheduled_posts.json" ]; then
    echo '[]' > data/scheduled_posts.json
    echo "✅ Initialized scheduled_posts.json"
fi

# Initialize posting_config.json
if [ ! -f "data/posting_config.json" ] || [ ! -s "data/posting_config.json" ]; then
    echo '{
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
            "auto_research_keywords": true,
            "auto_generate_images": true,
            "plagiarism_check": true
        },
        "seo_settings": {
            "keyword_density_min": 0.5,
            "keyword_density_max": 2.5,
            "internal_links": true,
            "external_links": true,
            "meta_description_auto": true
        }
    }' > data/posting_config.json
    echo "✅ Initialized posting_config.json"
fi

# Initialize bulk_titles.json
if [ ! -f "data/bulk_titles.json" ] || [ ! -s "data/bulk_titles.json" ]; then
    echo '[]' > data/bulk_titles.json
    echo "✅ Initialized bulk_titles.json"
fi

# Initialize api_keys.json
if [ ! -f "data/api_keys.json" ] || [ ! -s "data/api_keys.json" ]; then
    echo '{
        "openai_api_key": "",
        "hf_api_key": "",
        "blogger_blog_id": "",
        "google_client_id": "",
        "google_client_secret": "",
        "is_configured": false
    }' > data/api_keys.json
    echo "✅ Initialized api_keys.json"
fi

# Initialize advanced_config.json
if [ ! -f "data/advanced_config.json" ] || [ ! -s "data/advanced_config.json" ]; then
    echo '{
        "posting_strategies": {
            "peak_hours": ["09:00", "14:00", "19:00"],
            "best_days": ["monday", "wednesday", "friday"],
            "seasonal_topics": {
                "q1": ["investasi awal tahun", "prediksi crypto tahun ini"],
                "q2": ["tax crypto", "mid-year review"],
                "q3": ["persiapan akhir tahun", "market analysis"],
                "q4": ["wrap-up tahun", "prediksi tahun depan"]
            }
        },
        "content_templates": {
            "how_to": {
                "structure": ["intro", "langkah_demi_langkah", "tips", "kesimpulan"],
                "keywords": ["cara", "panduan", "tutorial", "langkah"]
            },
            "review": {
                "structure": ["overview", "kelebihan", "kekurangan", "verdict"],
                "keywords": ["review", "ulasan", "test", "analisis"]
            },
            "news": {
                "structure": ["berita_terkini", "dampak", "analisis", "prediksi"],
                "keywords": ["berita", "update", "terbaru", "trending"]
            }
        },
        "auto_posting_rules": {
            "min_interval_between_posts": 4,
            "max_posts_per_day": 3,
            "avoid_duplicate_topics": true,
            "auto_diversify_content_types": true
        }
    }' > data/advanced_config.json
    echo "✅ Initialized advanced_config.json"
fi

# Set proper permissions
chmod -R 755 data uploads static

echo "🎉 Build completed successfully!"
echo ""
echo "🔐 FIRST TIME SETUP INSTRUCTIONS:"
echo "   1. Access your app URL"
echo "   2. Enter ANY password as master key (remember it!)"
echo "   3. Go to Settings to configure API keys"
echo "   4. Start uploading titles and scheduling posts!"
echo ""
echo "📝 App will be available at: https://your-app-name.onrender.com"
