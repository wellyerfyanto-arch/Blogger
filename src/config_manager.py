import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.config_file = 'data/advanced_config.json'
        self.load_config()
    
    def load_config(self):
        """Load konfigurasi dari file"""
        default_config = {
            "posting_strategies": {
                "peak_hours": ["09:00", "14:00", "19:00"],
                "best_days": ["monday", "wednesday", "friday"],
                "seasonal_topics": {
                    "q1": ["investasi awal tahun", "prediksi crypto tahun ini", "strategi trading q1"],
                    "q2": ["tax crypto", "mid-year review", "persiapan bull run"],
                    "q3": ["persiapan akhir tahun", "market analysis q3", "portfolio review"],
                    "q4": ["wrap-up tahun", "prediksi tahun depan", "strategi tax loss harvesting"]
                },
                "content_calendar": {
                    "monthly_themes": {
                        "01": "Trading Strategy",
                        "02": "Blockchain Technology", 
                        "03": "DeFi & NFTs",
                        "04": "Market Analysis",
                        "05": "Crypto Security",
                        "06": "Investment Guide",
                        "07": "Altcoin Review",
                        "08": "Trading Tools",
                        "09": "Wallet Security",
                        "10": "Market Prediction",
                        "11": "Tax Planning",
                        "12": "Year in Review"
                    }
                }
            },
            "content_templates": {
                "how_to": {
                    "structure": ["intro", "langkah_demi_langkah", "tips", "kesimpulan"],
                    "keywords": ["cara", "panduan", "tutorial", "langkah", "step by step"],
                    "target_word_count": 1200
                },
                "review": {
                    "structure": ["overview", "kelebihan", "kekurangan", "verdict", "alternatives"],
                    "keywords": ["review", "ulasan", "test", "analisis", "perbandingan"],
                    "target_word_count": 1500
                },
                "news": {
                    "structure": ["berita_terkini", "dampak", "analisis", "prediksi", "takeaway"],
                    "keywords": ["berita", "update", "terbaru", "trending", "breaking news"],
                    "target_word_count": 800
                },
                "guide": {
                    "structure": ["pengenalan", "dasar_dasar", "advanced_tips", "common_mistakes", "resources"],
                    "keywords": ["panduan", "guide", "tutorial lengkap", "untuk pemula", "advanced"],
                    "target_word_count": 2000
                }
            },
            "auto_posting_rules": {
                "min_interval_between_posts": 4,
                "max_posts_per_day": 3,
                "avoid_duplicate_topics": True,
                "auto_diversify_content_types": True,
                "quality_threshold": 70,
                "auto_retry_failed_posts": True,
                "max_retry_attempts": 3
            },
            "seo_optimization": {
                "target_keyword_density": 1.5,
                "min_internal_links": 2,
                "min_external_links": 1,
                "heading_structure": ["h1", "h2", "h3", "h2", "h3", "h2", "conclusion"],
                "image_optimization": True,
                "mobile_friendly_check": True
            }
        }
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                # Merge dengan default config
                self.config = self.merge_dicts(default_config, saved_config)
                logger.info("Configuration loaded successfully")
        except FileNotFoundError:
            self.config = default_config
            self.save_config()
            logger.info("Created new configuration file")
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            self.config = default_config
    
    def merge_dicts(self, dict1: Dict, dict2: Dict) -> Dict:
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
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def get_optimal_posting_schedule(self, num_posts: int, start_date: datetime = None) -> List[str]:
        """Generate jadwal posting optimal berdasarkan rules"""
        if start_date is None:
            start_date = datetime.now()
        
        schedule = []
        current_time = start_date
        
        peak_hours = self.config["posting_strategies"]["peak_hours"]
        best_days = self.config["posting_strategies"]["best_days"]
        min_interval = self.config["auto_posting_rules"]["min_interval_between_posts"]
        max_per_day = self.config["auto_posting_rules"]["max_posts_per_day"]
        
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, 
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }
        
        best_day_nums = [day_map[day] for day in best_days]
        
        posts_scheduled = 0
        days_ahead = 0
        posts_today = 0
        
        while posts_scheduled < num_posts:
            target_date = current_time + timedelta(days=days_ahead)
            target_day_num = target_date.weekday()
            
            if target_day_num in best_day_nums:
                # Schedule posts untuk hari ini
                for hour in peak_hours:
                    if posts_scheduled >= num_posts:
                        break
                    if posts_today >= max_per_day:
                        break
                    
                    post_time = target_date.replace(
                        hour=int(hour.split(':')[0]),
                        minute=int(hour.split(':')[1]),
                        second=0,
                        microsecond=0
                    )
                    
                    # Pastikan waktu posting di masa depan
                    if post_time > current_time:
                        schedule.append(post_time.isoformat())
                        posts_scheduled += 1
                        posts_today += 1
            
            days_ahead += 1
            posts_today = 0
            
            # Batasi maksimal 90 hari ke depan
            if days_ahead > 90:
                break
        
        return schedule
    
    def suggest_content_type(self, title: str) -> str:
        """Saran tipe konten berdasarkan judul"""
        title_lower = title.lower()
        
        for content_type, template in self.config["content_templates"].items():
            for keyword in template["keywords"]:
                if keyword in title_lower:
                    return content_type
        
        # Default to guide jika tidak ada match
        return "guide"
    
    def get_seasonal_topics(self) -> List[str]:
        """Dapatkan topik musiman untuk kuartal saat ini"""
        current_quarter = (datetime.now().month - 1) // 3 + 1
        quarter_key = f"q{current_quarter}"
        return self.config["posting_strategies"]["seasonal_topics"].get(quarter_key, [])
    
    def get_monthly_theme(self) -> str:
        """Dapatkan tema bulanan"""
        current_month = datetime.now().strftime("%m")
        return self.config["posting_strategies"]["content_calendar"]["monthly_themes"].get(current_month, "General Crypto")
    
    def get_template_structure(self, content_type: str) -> List[str]:
        """Dapatkan struktur template untuk tipe konten"""
        return self.config["content_templates"].get(content_type, {}).get("structure", [])
    
    def get_target_word_count(self, content_type: str) -> int:
        """Dapatkan target word count untuk tipe konten"""
        return self.config["content_templates"].get(content_type, {}).get("target_word_count", 1000)
    
    def update_setting(self, section: str, key: str, value):
        """Update pengaturan tertentu"""
        if section in self.config and key in self.config[section]:
            self.config[section][key] = value
            self.save_config()
            return True
        return False

# Global instance
config_manager = ConfigManager()
