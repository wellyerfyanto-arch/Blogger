import json
import os
from datetime import datetime, timedelta

class ConfigManager:
    def __init__(self):
        self.config_file = 'advanced_config.json'
        self.load_config()
    
    def load_config(self):
        """Load konfigurasi dari file"""
        default_config = {
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
                "min_interval_between_posts": 4,  # jam
                "max_posts_per_day": 3,
                "avoid_duplicate_topics": True,
                "auto_diversify_content_types": True
            }
        }
        
        try:
            with open(self.config_file, 'r') as f:
                saved_config = json.load(f)
                # Merge dengan default config
                self.config = self.merge_dicts(default_config, saved_config)
        except FileNotFoundError:
            self.config = default_config
            self.save_config()
    
    def merge_dicts(self, dict1, dict2):
        """Merge dua dictionary recursively"""
        result = dict1.copy()
        for key, value in dict2.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self.merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_config(self):
        """Simpan konfigurasi ke file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_optimal_posting_schedule(self, num_posts):
        """Generate jadwal posting optimal berdasarkan rules"""
        schedule = []
        current_time = datetime.now()
        
        peak_hours = self.config["posting_strategies"]["peak_hours"]
        best_days = self.config["posting_strategies"]["best_days"]
        min_interval = self.config["auto_posting_rules"]["min_interval_between_posts"]
        
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, 
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }
        
        current_day = current_time.weekday()
        best_day_nums = [day_map[day] for day in best_days]
        
        posts_scheduled = 0
        days_ahead = 0
        
        while posts_scheduled < num_posts:
            target_day = (current_day + days_ahead) % 7
            
            if target_day in best_day_nums:
                # Schedule posts untuk hari ini
                for hour in peak_hours:
                    if posts_scheduled >= num_posts:
                        break
                    
                    post_time = current_time.replace(
                        day=current_time.day + days_ahead,
                        hour=int(hour.split(':')[0]),
                        minute=int(hour.split(':')[1]),
                        second=0,
                        microsecond=0
                    )
                    
                    # Pastikan waktu posting di masa depan
                    if post_time > current_time:
                        schedule.append(post_time.isoformat())
                        posts_scheduled += 1
            
            days_ahead += 1
            
            # Batasi maksimal 30 hari ke depan
            if days_ahead > 30:
                break
        
        return schedule
    
    def suggest_content_type(self, title):
        """Saran tipe konten berdasarkan judul"""
        title_lower = title.lower()
        
        for content_type, template in self.config["content_templates"].items():
            for keyword in template["keywords"]:
                if keyword in title_lower:
                    return content_type
        
        return "general"
    
    def get_seasonal_topics(self):
        """Dapatkan topik musiman untuk kuartal saat ini"""
        current_quarter = (datetime.now().month - 1) // 3 + 1
        quarter_key = f"q{current_quarter}"
        return self.config["posting_strategies"]["seasonal_topics"].get(quarter_key, [])

config_manager = ConfigManager()
