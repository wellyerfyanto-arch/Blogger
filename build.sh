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

# Create initial data files if they don't exist
echo "📊 Initializing data files..."

# Create empty JSON files if they don't exist
for file in scheduled_posts posting_config bulk_titles advanced_config api_keys; do
    if [ ! -f "data/${file}.json" ]; then
        echo '{}' > "data/${file}.json"
        echo "✅ Created ${file}.json"
    fi
done

# Initialize specific config files with proper content
if [ ! -s "data/posting_config.json" ]; then
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
fi

if [ ! -s "data/api_keys.json" ]; then
    echo '{
        "openai_api_key": "",
        "hf_api_key": "",
        "blogger_blog_id": "",
        "google_client_id": "",
        "google_client_secret": "",
        "is_configured": false
    }' > data/api_keys.json
fi

# Initialize empty arrays for posts and titles
if [ ! -s "data/scheduled_posts.json" ]; then
    echo '[]' > data/scheduled_posts.json
fi

if [ ! -s "data/bulk_titles.json" ]; then
    echo '[]' > data/bulk_titles.json
fi

echo "🎉 Build completed successfully!"
echo "🔐 Application ready for deployment!"
