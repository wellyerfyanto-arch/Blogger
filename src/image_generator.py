import requests
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def generate_image_prompt(title: str) -> str:
    """
    Generate AI image prompt berdasarkan judul artikel
    """
    prompt_template = f"""
    Create a professional digital art illustration for a cryptocurrency blog article about: {title}
    
    Style: modern digital art, professional
    Theme: cryptocurrency, blockchain, technology, finance
    Mood: informative, futuristic, trustworthy
    Colors: blue, orange, purple, gradient
    Elements: crypto symbols, data visualization, digital elements
    Composition: balanced, clean, professional
    Aspect Ratio: 16:9 landscape
    
    Important: No text in the image, professional quality
    """
    
    return prompt_template

def create_image(prompt: str) -> Optional[str]:
    """
    Generate gambar menggunakan Hugging Face API (gratis)
    """
    API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
    
    try:
        response = requests.post(
            API_URL, 
            headers=headers, 
            json={"inputs": prompt},
            timeout=30
        )
        
        if response.status_code == 200:
            # Save image locally
            import hashlib
            image_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
            image_path = f"static/images/generated_{image_hash}.jpg"
            
            with open(image_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Image generated: {image_path}")
            return f"/{image_path}"
        else:
            logger.error(f"Image generation failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Image generation error: {str(e)}")
        return None

def get_fallback_image() -> str:
    """
    Return fallback image URL
    """
    return "/static/images/placeholder.jpg"
