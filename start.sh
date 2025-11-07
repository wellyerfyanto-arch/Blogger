#!/bin/bash
echo "🚀 Starting Auto Posting Blog Application..."
echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "🔧 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Starting Gunicorn..."
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
