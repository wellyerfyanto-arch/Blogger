import openai
import os
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def generate_article(title: str, keywords: List[str] = None) -> Dict:
    """
    Generate SEO-optimized article based on title and keywords
    """
    try:
        # Riset kata kunci jika tidak disediakan
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

def research_keywords(title: str) -> List[str]:
    """
    Lakukan riset kata kunci sederhana berdasarkan judul
    """
    base_keywords = extract_keywords_from_title(title)
    
    # Tambahkan long-tail keywords
    modifiers = ["untuk pemula", "panduan lengkap", "cara mudah", "tips dan trik", "terbaru 2024"]
    long_tail = [f"{kw} {mod}" for kw in base_keywords for mod in modifiers][:8]
    
    return base_keywords + long_tail

def extract_keywords_from_title(title: str) -> List[str]:
    """
    Ekstrak kata kunci utama dari judul
    """
    stop_words = {"dan", "atau", "di", "ke", "dari", "untuk", "pada", "dengan", "yang", "ada"}
    words = re.findall(r'\b\w+\b', title.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return list(dict.fromkeys(keywords))[:5]  # Remove duplicates

def parse_generated_content(content: str, keywords: List[str]) -> Dict:
    """
    Parse konten yang di-generate menjadi structured data
    """
    lines = content.split('\n')
    result = {
        "title": "",
        "meta_description": "",
        "content": "",
        "keywords": keywords,
        "word_count": 0
    }
    
    current_section = None
    for line in lines:
        if line.startswith('JUDUL:'):
            result["title"] = line.replace('JUDUL:', '').strip()
        elif line.startswith('META_DESCRIPTION:'):
            result["meta_description"] = line.replace('META_DESCRIPTION:', '').strip()
        elif line.startswith('KONTEN:'):
            current_section = "content"
            result["content"] = line.replace('KONTEN:', '').strip()
        elif current_section == "content":
            result["content"] += '\n' + line
    
    # Hitung jumlah kata
    result["word_count"] = len(result["content"].split())
    
    return result

def get_fallback_content(title: str, keywords: List[str]) -> Dict:
    """
    Fallback content jika AI gagal generate
    """
    return {
        "title": title,
        "meta_description": f"Artikel lengkap tentang {title}. Pelajari selengkapnya di sini.",
        "content": f"""
        # {title}
        
        ## Pengenalan
        Artikel ini membahas tentang {title} secara mendetail. 
        
        ## Poin Penting
        - Pemahaman dasar tentang topik
        - Implementasi praktis
        - Tips dan best practices
        
        ## Kesimpulan
        {title} adalah topik yang penting untuk dipahami dalam dunia cryptocurrency.
        
        Mulai perjalanan crypto Anda hari ini!
        """,
        "keywords": keywords or [title],
        "word_count": 250
      }
