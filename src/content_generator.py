import openai
import os
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def get_openai_key():
    """Get OpenAI API key from environment or API keys manager"""
    # Try environment first (for Render env vars)
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key:
        return env_key
    
    # Try to load from API keys file
    try:
        with open('data/api_keys.json', 'r') as f:
            api_keys = json.load(f)
        return api_keys.get('openai_api_key', '')
    except Exception as e:
        logger.warning(f"Could not load OpenAI key from file: {str(e)}")
        return ''

def generate_article(title: str, keywords: List[str] = None) -> Dict:
    """
    Generate SEO-optimized article based on title and keywords
    """
    try:
        # Get API key
        api_key = get_openai_key()
        if not api_key:
            raise Exception("OpenAI API key not configured")
        
        openai.api_key = api_key
        
        # Research keywords if not provided
        if not keywords:
            keywords = research_keywords(title)
        
        # Prompt untuk GPT
        prompt = f"""
        Buat artikel blog SEO-optimized tentang '{title}' dengan spesifikasi:
        
        PANJANG: Minimal 1000 kata
        STRUKTUR: 
        - Pendahuluan yang menarik
        - Minimal 5 subheading (H2, H3)
        - Paragraf pendek (2-3 kalimat)
        - Bullet points/numbered lists
        - Kesimpulan yang kuat
        
        SEO REQUIREMENTS:
        - Kata kunci utama: {keywords[0] if keywords else title}
        - Kata kunci sekunder: {', '.join(keywords[1:]) if len(keywords) > 1 else 'N/A'}
        - Density kata kunci: 1-2%
        - Internal links suggestion
        - External links to authoritative sources
        
        TONE: Informatif, engaging, mudah dipahami pemula
        TARGET: Pembaca Indonesia usia 18-45
        
        Format response:
        JUDUL: [judul artikel]
        META_DESCRIPTION: [150-160 karakter]
        KONTEN: [konten lengkap dengan formatting]
        KEYWORDS: [daftar kata kunci]
        """
        
        # Panggil OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Anda adalah penulis konten ahli cryptocurrency dan SEO specialist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3500,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        return parse_generated_content(content, keywords)
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return get_fallback_content(title, keywords)

# ... (rest of the functions remain the same)
