import os
import pickle
import html
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

# Scope untuk Blogger API
SCOPES = ['https://www.googleapis.com/auth/blogger']

def authenticate_blogger():
    """
    Autentikasi dengan Blogger API menggunakan service account atau OAuth
    """
    creds = None
    
    # Cek jika menggunakan service account
    if os.path.exists('service_account.json'):
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', scopes=SCOPES
        )
        return creds
    
    # OAuth flow untuk personal account
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def post_to_blogger(title: str, content: str, meta_description: str = "", 
                   image_url: str = "", keywords: list = None) -> str:
    """
    Post artikel ke Blogger platform
    """
    try:
        creds = authenticate_blogger()
        service = build('blogger', 'v3', credentials=creds)
        
        # Format konten untuk Blogger
        html_content = format_blogger_content(content, image_url, meta_description)
        
        # Data postingan
        blog_id = os.getenv('BLOGGER_BLOG_ID')
        post_body = {
            'title': title,
            'content': html_content,
            'labels': keywords or [],
            'customMetaData': meta_description
        }
        
        # Execute API call
        posts = service.posts()
        insert_request = posts.insert(blogId=blog_id, body=post_body)
        result = insert_request.execute()
        
        logger.info(f"Successfully posted to Blogger: {result.get('url')}")
        return result.get('url', '')
        
    except HttpError as error:
        logger.error(f"Blogger API error: {error}")
        raise Exception(f"Blogger API error: {error}")
    except Exception as e:
        logger.error(f"Error posting to Blogger: {str(e)}")
        raise Exception(f"Error posting to Blogger: {str(e)}")

def format_blogger_content(content: str, image_url: str = "", meta_description: str = "") -> str:
    """
    Format konten untuk Blogger dengan optimasi SEO dan mobile
    """
    html_content = ""
    
    # Tambahkan featured image jika ada
    if image_url:
        html_content += f'''
        <div class="featured-image" style="text-align: center; margin-bottom: 20px;">
            <img src="{image_url}" alt="Featured Image" 
                 style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        </div>
        '''
    
    # Tambahkan meta description sebagai excerpt
    if meta_description:
        html_content += f'''
        <div class="article-excerpt" style="font-style: italic; color: #666; font-size: 1.1em; 
              padding: 15px; background: #f8f9fa; border-left: 4px solid #667eea; margin-bottom: 20px;">
            {html.escape(meta_description)}
        </div>
        '''
    
    # Konversi markdown-like content ke HTML
    lines = content.split('\n')
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_content += '</ul>\n'
                in_list = False
            continue
            
        # Heading level 2
        if line.startswith('## '):
            if in_list:
                html_content += '</ul>\n'
                in_list = False
            html_content += f'<h2>{html.escape(line[3:])}</h2>\n'
        
        # Heading level 3
        elif line.startswith('### '):
            if in_list:
                html_content += '</ul>\n'
                in_list = False
            html_content += f'<h3>{html.escape(line[4:])}</h3>\n'
        
        # List items
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                html_content += '<ul>\n'
                in_list = True
            html_content += f'<li>{html.escape(line[2:])}</li>\n'
        
        # Regular paragraph
        else:
            if in_list:
                html_content += '</ul>\n'
                in_list = False
            html_content += f'<p>{html.escape(line)}</p>\n'
    
    # Close any open list
    if in_list:
        html_content += '</ul>\n'
    
    # Add responsive CSS
    responsive_css = '''
    <style>
    @media (max-width: 768px) {
        .featured-image img { 
            max-width: 100% !important; 
            height: auto !important; 
        }
        h2 { font-size: 1.5em !important; }
        h3 { font-size: 1.3em !important; }
        p, li { 
            font-size: 1.1em !important; 
            line-height: 1.6 !important; 
        }
        .article-excerpt {
            font-size: 1em !important;
            padding: 10px !important;
        }
    }
    </style>
    '''
    
    return responsive_css + html_content
