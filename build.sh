#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data uploads static/images

# Create initial data files
if [ ! -f data/scheduled_posts.json ]; then
    echo '[]' > data/scheduled_posts.json
fi

if [ ! -f data/posting_config.json ]; then
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

if [ ! -f data/bulk_titles.json ]; then
    echo '[]' > data/bulk_titles.json
fi

if [ ! -f data/advanced_config.json ]; then
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
fi

echo "Build completed successfully!"
