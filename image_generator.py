import requests
import os
from typing import Optional

def generate_image_prompt(title: str) -> str:
    """
    Generate prompt untuk gambar berdasarkan judul artikel
    """
    prompt_template = f"""
    Buat prompt untuk AI image generator untuk artikel tentang: {title}
    
    Kriteria:
    - Style: digital art, modern, professional
    - Theme: cryptocurrency, blockchain, technology
    - Mood: informative, futuristic, trustworthy
    - Elements: crypto symbols, data visualization, technology elements
    - Color scheme: blue, orange, purple (warna khas crypto)
    - Aspect ratio: 16:9 (landscape)
    
    Hasilkan prompt dalam bahasa Inggris yang detail.
    """
    
    # Gunakan OpenAI untuk generate prompt yang lebih baik
    try:
        import openai
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Anda ahli dalam membuat prompt untuk AI image generator."},
                {"role": "user", "content": prompt_template}
            ],
            max_tokens=200,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except:
        # Fallback prompt
        return f"Professional digital art illustration about {title}, cryptocurrency blockchain technology, futuristic style, blue orange color scheme, landscape 16:9"

def create_image(prompt: str) -> Optional[str]:
    """
    Generate gambar menggunakan AI model open source (Stable Diffusion)
    Menggunakan Hugging Face API gratis
    """
    API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
    
    try:
        response = requests.post(
            API_URL, 
            headers=headers, 
            json={"inputs": prompt}
        )
        
        if response.status_code == 200:
            # Simpan gambar dan return URL
            image_path = f"static/generated_{hash(prompt)}.jpg"
            with open(image_path, "wb") as f:
                f.write(response.content)
            return f"/{image_path}"
        else:
            print(f"Error generating image: {response.text}")
            return None
            
    except Exception as e:
        print(f"Image generation failed: {str(e)}")
        return None
