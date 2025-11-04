import re
from typing import Dict

def analyze_seo(content: str, title: str) -> Dict:
    """
    Analisis konten untuk optimasi SEO
    """
    analysis = {
        "score": 0,
        "word_count": len(content.split()),
        "headings": {},
        "keyword_density": {},
        "readability": {},
        "recommendations": []
    }
    
    # Analisis heading structure
    analysis["headings"] = analyze_headings(content)
    
    # Analisis keyword density
    analysis["keyword_density"] = analyze_keyword_density(content, title)
    
    # Analisis readability
    analysis["readability"] = analyze_readability(content)
    
    # Hitung overall score
    analysis["score"] = calculate_seo_score(analysis)
    
    # Generate recommendations
    analysis["recommendations"] = generate_recommendations(analysis)
    
    return analysis

def analyze_headings(content: str) -> Dict:
    """
    Analisis struktur heading
    """
    headings = {
        "h1": len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE)),
        "h2": len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE)),
        "h3": len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
    }
    return headings

def analyze_keyword_density(content: str, title: str) -> Dict:
    """
    Analisis density kata kunci
    """
    # Ekstrak kata kunci dari title
    keywords = re.findall(r'\b\w+\b', title.lower())
    keywords = [kw for kw in keywords if len(kw) > 3][:5]
    
    content_lower = content.lower()
    total_words = len(content_lower.split())
    
    density = {}
    for keyword in keywords:
        count = content_lower.count(keyword)
        density[keyword] = {
            "count": count,
            "density": (count / total_words) * 100 if total_words > 0 else 0
        }
    
    return density

def analyze_readability(content: str) -> Dict:
    """
    Analisis tingkat keterbacaan
    """
    words = content.split()
    sentences = re.split(r'[.!?]+', content)
    
    avg_sentence_length = len(words) / len(sentences) if sentences else 0
    avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
    
    return {
        "avg_sentence_length": avg_sentence_length,
        "avg_word_length": avg_word_length,
        "reading_level": "Sedang" if 15 <= avg_sentence_length <= 20 else "Sulit" if avg_sentence_length > 20 else "Mudah"
    }

def calculate_seo_score(analysis: Dict) -> int:
    """
    Hitung skor SEO overall
    """
    score = 0
    
    # Poin untuk word count
    if analysis["word_count"] >= 1000:
        score += 25
    elif analysis["word_count"] >= 500:
        score += 15
    
    # Poin untuk heading structure
    if analysis["headings"]["h2"] >= 3:
        score += 20
    
    # Poin untuk readability
    if analysis["readability"]["reading_level"] == "Sedang":
        score += 25
    
    # Poin untuk keyword density
    good_density = sum(1 for kw in analysis["keyword_density"].values() 
                      if 0.5 <= kw["density"] <= 2.5)
    score += min(good_density * 10, 30)
    
    return min(score, 100)

def generate_recommendations(analysis: Dict) -> list:
    """
    Generate rekomendasi perbaikan SEO
    """
    recommendations = []
    
    if analysis["word_count"] < 1000:
        recommendations.append("Tambah panjang konten hingga minimal 1000 kata")
    
    if analysis["headings"]["h2"] < 3:
        recommendations.append("Tambahkan lebih banyak subheading (H2)")
    
    if analysis["readability"]["avg_sentence_length"] > 25:
        recommendations.append("Perpendek kalimat untuk meningkatkan keterbacaan")
    
    # Cek keyword density
    for keyword, data in analysis["keyword_density"].items():
        if data["density"] < 0.5:
            recommendations.append(f"Tingkatkan penggunaan kata kunci '{keyword}'")
        elif data["density"] > 2.5:
            recommendations.append(f"Kurangi penggunaan kata kunci '{keyword}' yang berlebihan")
    
    return recommendations
