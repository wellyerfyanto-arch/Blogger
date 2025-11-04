import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def analyze_seo(content: str, title: str, keywords: List[str] = None) -> Dict:
    """
    Analisis SEO komprehensif untuk konten
    """
    analysis = {
        "score": 0,
        "word_count": len(content.split()),
        "headings": {},
        "keyword_analysis": {},
        "readability": {},
        "technical_seo": {},
        "recommendations": []
    }
    
    # Analisis struktur heading
    analysis["headings"] = analyze_headings(content)
    
    # Analisis kata kunci
    analysis["keyword_analysis"] = analyze_keywords(content, title, keywords)
    
    # Analisis keterbacaan
    analysis["readability"] = analyze_readability(content)
    
    # Analisis teknikal SEO
    analysis["technical_seo"] = analyze_technical_seo(content)
    
    # Hitung skor overall
    analysis["score"] = calculate_seo_score(analysis)
    
    # Generate rekomendasi
    analysis["recommendations"] = generate_recommendations(analysis)
    
    return analysis

def analyze_headings(content: str) -> Dict:
    """
    Analisis struktur heading H1, H2, H3
    """
    headings = {
        "h1": len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE)),
        "h2": len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE)),
        "h3": len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE)),
        "structure_score": 0
    }
    
    # Hitung skor struktur heading
    if headings["h1"] == 1:
        headings["structure_score"] += 25
    if headings["h2"] >= 3:
        headings["structure_score"] += 50
    if headings["h3"] >= 2:
        headings["structure_score"] += 25
    
    return headings

def analyze_keywords(content: str, title: str, keywords: List[str] = None) -> Dict:
    """
    Analisis penggunaan kata kunci
    """
    if not keywords:
        keywords = extract_keywords_from_title(title)
    
    content_lower = content.lower()
    total_words = len(content_lower.split())
    
    keyword_analysis = {}
    for keyword in keywords[:10]:  # Batasi analisis untuk 10 keywords
        count = content_lower.count(keyword.lower())
        density = (count / total_words) * 100 if total_words > 0 else 0
        
        keyword_analysis[keyword] = {
            "count": count,
            "density": round(density, 2),
            "score": calculate_keyword_score(density)
        }
    
    return keyword_analysis

def analyze_readability(content: str) -> Dict:
    """
    Analisis tingkat keterbacaan konten
    """
    # Hapus HTML tags untuk analisis teks murni
    clean_content = re.sub(r'<[^>]+>', '', content)
    sentences = re.split(r'[.!?]+', clean_content)
    words = clean_content.split()
    
    avg_sentence_length = len(words) / len(sentences) if sentences else 0
    avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
    
    # Hitung Flesch Reading Ease (approximation)
    readability_score = max(0, min(100, 206.835 - (1.015 * avg_sentence_length) - (84.6 * (avg_word_length / 100))))
    
    if readability_score >= 60:
        reading_level = "Mudah"
    elif readability_score >= 50:
        reading_level = "Sedang"
    elif readability_score >= 30:
        reading_level = "Agak Sulit"
    else:
        reading_level = "Sulit"
    
    return {
        "avg_sentence_length": round(avg_sentence_length, 1),
        "avg_word_length": round(avg_word_length, 1),
        "readability_score": round(readability_score, 1),
        "reading_level": reading_level
    }

def analyze_technical_seo(content: str) -> Dict:
    """
    Analisis aspek teknikal SEO
    """
    # Cek internal links
    internal_links = len(re.findall(r'href="[^"]*cryptoajah', content, re.IGNORECASE))
    
    # Cek external links
    external_links = len(re.findall(r'href="https?://(?!cryptoajah)[^"]+', content, re.IGNORECASE))
    
    # Cek image alt tags
    images_with_alt = len(re.findall(r'<img[^>]*alt="[^"]*"[^>]*>', content, re.IGNORECASE))
    total_images = len(re.findall(r'<img[^>]*>', content, re.IGNORECASE))
    
    return {
        "internal_links": internal_links,
        "external_links": external_links,
        "images_with_alt": images_with_alt,
        "total_images": total_images,
        "image_alt_score": (images_with_alt / total_images * 100) if total_images > 0 else 100
    }

def calculate_seo_score(analysis: Dict) -> int:
    """
    Hitung skor SEO overall (0-100)
    """
    score = 0
    
    # Word count (25 points)
    if analysis["word_count"] >= 1000:
        score += 25
    elif analysis["word_count"] >= 500:
        score += 15
    elif analysis["word_count"] >= 300:
        score += 5
    
    # Heading structure (25 points)
    score += min(analysis["headings"]["structure_score"], 25)
    
    # Keyword optimization (25 points)
    good_keywords = sum(1 for kw in analysis["keyword_analysis"].values() 
                       if 0.5 <= kw["density"] <= 2.5)
    score += min(good_keywords * 5, 25)
    
    # Readability (15 points)
    if analysis["readability"]["reading_level"] in ["Mudah", "Sedang"]:
        score += 15
    elif analysis["readability"]["reading_level"] == "Agak Sulit":
        score += 8
    
    # Technical SEO (10 points)
    if analysis["technical_seo"]["internal_links"] >= 2:
        score += 5
    if analysis["technical_seo"]["external_links"] >= 1:
        score += 3
    if analysis["technical_seo"]["image_alt_score"] >= 80:
        score += 2
    
    return min(score, 100)

def generate_recommendations(analysis: Dict) -> List[str]:
    """
    Generate rekomendasi perbaikan SEO
    """
    recommendations = []
    
    # Word count recommendations
    if analysis["word_count"] < 1000:
        recommendations.append(f"Tambah panjang konten dari {analysis['word_count']} menjadi minimal 1000 kata")
    
    # Heading recommendations
    if analysis["headings"]["h1"] != 1:
        recommendations.append("Pastikan ada tepat satu H1 heading")
    if analysis["headings"]["h2"] < 3:
        recommendations.append("Tambahkan lebih banyak subheading H2 (minimal 3)")
    
    # Keyword recommendations
    for keyword, data in analysis["keyword_analysis"].items():
        if data["density"] < 0.5:
            recommendations.append(f"Tingkatkan penggunaan kata kunci '{keyword}'")
        elif data["density"] > 2.5:
            recommendations.append(f"Kurangi penggunaan kata kunci '{keyword}' yang berlebihan")
    
    # Readability recommendations
    if analysis["readability"]["reading_level"] in ["Agak Sulit", "Sulit"]:
        recommendations.append("Sederhanakan kalimat untuk meningkatkan keterbacaan")
    
    # Technical recommendations
    if analysis["technical_seo"]["internal_links"] < 2:
        recommendations.append("Tambahkan lebih banyak internal links")
    if analysis["technical_seo"]["external_links"] < 1:
        recommendations.append("Tambahkan external links ke sumber authoritative")
    if analysis["technical_seo"]["image_alt_score"] < 100:
        recommendations.append("Tambahkan alt text pada semua gambar")
    
    return recommendations[:10]  # Batasi 10 rekomendasi

def extract_keywords_from_title(title: str) -> List[str]:
    """
    Ekstrak kata kunci dari judul
    """
    stop_words = {"dan", "atau", "di", "ke", "dari", "untuk", "pada", "dengan", "yang", "ada"}
    words = re.findall(r'\b\w+\b', title.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords[:5]

def calculate_keyword_score(density: float) -> int:
    """
    Hitung skor untuk density kata kunci (0-10)
    """
    if 0.5 <= density <= 2.5:
        return 10
    elif 0.3 <= density < 0.5 or 2.5 < density <= 3.0:
        return 5
    else:
        return 0
