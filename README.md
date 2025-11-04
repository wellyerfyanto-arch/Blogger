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
