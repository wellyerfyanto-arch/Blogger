import openai
import os
import re
from typing import List, Dict

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_article(title: str, keywords: List[str] = None) -> Dict:
    """
    Generate artikel SEO optimized berdasarkan judul dan kata kunci
    """
    
    # Riset kata kunci jika tidak disediakan
    if not keywords:
        keywords = research_keywords(title)
    
    # Generate konten dengan GPT
    prompt = f"""
    Buat artikel blog tentang '{title}' dengan spesifikasi berikut:
    
    1. Panjang minimal 1000 kata
    2. Optimasi SEO dengan kata kunci: {', '.join(keywords)}
    3. Struktur yang mudah dibaca dengan heading H2, H3
    4. Paragraf pendek (2-3 kalimat per paragraf)
    5. Sisipkan bullet points atau numbered list
    6. Gunakan long-tail keywords secara natural
    7. Tambahkan call-to-action
    8. Konten evergreen (tidak cepat kadaluarsa)
    9. Tone: informatif namun engaging
    10. Target pembaca: pemula hingga menengah
    
    Format respons:
    - Judul: [judul artikel]
    - Meta Description: [deskripsi 150-160 karakter]
    - Konten: [konten artikel lengkap]
    - Keywords: [daftar kata kunci utama]
    - Internal Links: [saran link internal dari cryptoajah.blogspot.com]
    - External Links: [saran link eksternal authoritative]
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Anda adalah penulis konten SEO specialist di bidang cryptocurrency."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        return parse_generated_content(content, keywords)
        
    except Exception as e:
        raise Exception(f"Error generating content: {str(e)}")

def research_keywords(title: str) -> List[str]:
    """
    Lakukan riset kata kunci berdasarkan judul
    """
    # Implementasi sederhana riset keyword
    base_keywords = extract_keywords_from_title(title)
    
    # Tambahkan long-tail keywords
    long_tail_keywords = [
        f"{kw} untuk pemula" for kw in base_keywords
    ] + [
        f"panduan {kw}" for kw in base_keywords
    ] + [
        f"cara {kw}" for kw in base_keywords if "cara" not in kw.lower()
    ]
    
    return base_keywords + long_tail_keywords[:5]  # Batasi jumlah keywords

def extract_keywords_from_title(title: str) -> List[str]:
    """
    Ekstrak kata kunci utama dari judul
    """
    stop_words = {"dan", "atau", "di", "ke", "dari", "untuk", "pada", "dengan"}
    words = re.findall(r'\b\w+\b', title.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords[:10]  # Batasi ke 10 keywords utama

def parse_generated_content(content: str, keywords: List[str]) -> Dict:
    """
    Parse konten yang di-generate menjadi struktur yang terorganisir
    """
    sections = content.split('\n\n')
    result = {
        "title": "",
        "meta_description": "",
        "content": "",
        "keywords": keywords,
        "word_count": 0
    }
    
    current_section = ""
    for section in sections:
        if section.startswith("Judul:"):
            result["title"] = section.replace("Judul:", "").strip()
        elif section.startswith("Meta Description:"):
            result["meta_description"] = section.replace("Meta Description:", "").strip()
        elif section.startswith("Konten:") or section.startswith("Content:"):
            current_section = "content"
            result["content"] = section.replace("Konten:", "").replace("Content:", "").strip()
        elif current_section == "content":
            result["content"] += "\n\n" + section
    
    # Hitung jumlah kata
    result["word_count"] = len(result["content"].split())
    
    return result
