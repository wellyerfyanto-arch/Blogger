# Auto Poster 🤖

Sistem auto posting otomatis untuk blog cryptocurrency dengan AI-powered content generation.

## ✨ Fitur Utama

- ✅ Auto generate artikel 1000+ kata
- ✅ Riset kata kunci otomatis
- ✅ Optimasi SEO lengkap
- ✅ Generate gambar AI
- ✅ Bulk upload judul
- ✅ Penjadwalan otomatis
- ✅ Integrasi Blogger API
- ✅ Mobile-friendly dashboard

## 🚀 Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 📋 Prerequisites

- Python 3.11+
- Blogger account
- OpenAI API key
- Hugging Face API key

## 🔧 Installation

```bash
git clone https://github.com/username/crypto-auto-poster.git
cd crypto-auto-poster
pip install -r requirements.txt
cp .env.example .env
# Edit .env dengan API keys Anda

🛠️ Development
bash
python app.py
Buka http://localhost:5000

📝 License
MIT License

🤝 Contributing
Pull requests are welcome!

API Keys Setup
OpenAI API
Visit https://platform.openai.com
Add to .env: OPENAI_API_KEY=your_key

Hugging Face API
Visit https://huggingface.co/
Create account and get API key
Add to .env: HF_API_KEY=your_key

Blogger API
Go to https://console.cloud.google.com/
Create new project
Enable Blogger API
Create OAuth 2.0 credentials
Download credentials.json

### **20. docs/deployment.md**
```markdown
# Deployment Guide

## Deploy to Render

### 1. Prepare Repository
- Push code to GitHub
- Ensure all files are committed

### 2. Create Render Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure service:

**Basic Settings:**
- Name: `crypto-auto-poster`
- Environment: `Python`
- Region: `Singapore`
- Branch: `main`

**Build Settings:**
- Build Command: `./build.sh`
- Start Command: `gunicorn app:app`

### 3. Environment Variables
Add these in Render dashboard:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | `generate-random-key` |
| `OPENAI_API_KEY` | `your-openai-key` |
| `HF_API_KEY` | `your-hf-key` |
| `BLOGGER_BLOG_ID` | `your-blog-id` |
| `GOOGLE_CLIENT_ID` | `your-google-client-id` |
| `GOOGLE_CLIENT_SECRET` | `your-google-client-secret` |

### 4. Deploy
- Click "Create Web Service"
- Wait for build to complete
- Your app will be live at `https://crypto-auto-poster.onrender.com`

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure requirements.txt is correct
- Verify build.sh has execute permissions

### App Crashes
- Check runtime logs
- Verify environment variables
- Ensure all dependencies are in requirements.txt

### Scheduler Not Working
- Check background thread is running
- Verify system timezone
- Check schedule configuration


### **2. .gitignore**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Environment variables
.env
.env.local
.env.production

# Data files
data/
uploads/
*.json
!samples/*.json

# API credentials
credentials.json
token.pickle
client_secrets.json

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Render
.render.yaml
