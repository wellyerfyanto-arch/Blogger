import requests
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_hf_key():
    """Get Hugging Face API key from environment or API keys manager"""
    # Try environment first (for Render env vars)
    env_key = os.getenv('HF_API_KEY')
    if env_key:
        return env_key
    
    # Try to load from API keys file
    try:
        with open('data/api_keys.json', 'r') as f:
            api_keys = json.load(f)
        return api_keys.get('hf_api_key', '')
    except Exception as e:
        logger.warning(f"Could not load HF key from file: {str(e)}")
        return ''

def create_image(prompt: str) -> Optional[str]:
    """
    Generate gambar menggunakan Hugging Face API
    """
    api_key = get_hf_key()
    if not api_key:
        logger.error("Hugging Face API key not configured")
        return None
    
    API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    headers = {"Authorization": f"Bearer {api_key}"}
    
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

# ... (rest of the functions remain the same)
