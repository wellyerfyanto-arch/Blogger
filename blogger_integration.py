import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import html

# Scope untuk Blogger API
SCOPES = ['https://www.googleapis.com/auth/blogger']

def authenticate_blogger():
    """
    Autentikasi dengan Blogger API
    """
    creds = None
    
    # File token menyimpan akses dan refresh token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Jika tidak ada credentials valid, minta user login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Simpan credentials untuk penggunaan berikutnya
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def post_to_blogger(title: str, content: str, meta_description: str = "", 
                   image_url: str = "", keywords: list = None) -> str:
    """
    Post artikel ke Blogger
    """
    try:
        creds = authenticate_blogger()
        service = build('blogger', 'v3', credentials=creds)
        
        # Siapkan konten HTML
        html_content = format_blogger_content(content, image_url, meta_description)
        
        # Data postingan
        blog_id = os.getenv('BLOGGER_BLOG_ID')  # ID blog dari URL
        post_body = {
            'title': title,
            'content': html_content,
            'labels': keywords or []
        }
        
        # Buat postingan
        posts = service.posts()
        insert_request = posts.insert(blogId=blog_id, body=post_body)
        result = insert_request.execute()
        
        return result.get('url', '')
        
    except Exception as e:
        raise Exception(f"Error posting to Blogger: {str(e)}")

def format_blogger_content(content: str, image_url: str = "", meta_description: str = "") -> str:
    """
    Format konten untuk Blogger dengan optimasi SEO dan mobile-friendly
    """
    html_content = ""
    
    # Tambahkan featured image jika ada
    if image_url:
        html_content += f'<div class="featured-image"><img src="{image_url}" alt="Featured Image" style="width:100%; max-width:800px; height:auto; border-radius:8px;"></div>\n\n'
    
    # Tambahkan meta description sebagai excerpt
    if meta_description:
        html_content += f'<p class="article-excerpt" style="font-style: italic; color: #666; font-size: 1.1em;">{html.escape(meta_description)}</p>\n\n'
    
    # Konversi markdown ke HTML dan optimasi
    lines = content.split('\n')
    for line in lines:
        if line.strip():
            # Format heading
            if line.startswith('## '):
                html_content += f'<h2>{html.escape(line[3:].strip())}</h2>\n\n'
            elif line.startswith('### '):
                html_content += f'<h3>{html.escape(line[4:].strip())}</h3>\n\n'
            # Format list
            elif line.startswith('- ') or line.startswith('* '):
                if not html_content.endswith('<ul>'):
                    html_content += '<ul>\n'
                html_content += f'<li>{html.escape(line[2:].strip())}</li>\n'
            else:
                # Tutup ul jika ada
                if html_content.endswith('</li>\n') and not line.startswith('- ') and not line.startswith('* '):
                    html_content += '</ul>\n\n'
                # Paragraf biasa
                html_content += f'<p>{html.escape(line.strip())}</p>\n\n'
    
    # CSS inline untuk mobile-friendly
    mobile_css = """
    <style>
    @media (max-width: 768px) {
        .featured-image img { max-width: 100% !important; }
        h2 { font-size: 1.5em; }
        h3 { font-size: 1.3em; }
        p, li { font-size: 1.1em; line-height: 1.6; }
    }
    </style>
    """
    
    return mobile_css + html_content
