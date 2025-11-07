#!/bin/bash
set -e  # Exit on error

echo "🚀 Starting build process on Render..."

# Upgrade pip first
python -m pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data uploads static/images templates static/samples

# Create initial data files with proper content
echo "📊 Initializing data files..."

# ... (bagian sebelumnya tetap sama)

# Set proper permissions
chmod -R 755 data uploads static

echo "🎉 Build completed successfully!"
echo ""
echo "🔧 SCHEDULER SETUP:"
echo "   - Scheduler will auto-start with the application"
echo "   - Check scheduler status in the dashboard"
echo "   - Use 'Trigger Now' to test immediately"
echo "   - Posts scheduled for today or earlier will be published automatically"
echo ""
echo "🔐 FIRST TIME SETUP:"
echo "   1. Access your app URL"
echo "   2. Enter ANY password as master key (remember it!)"
echo "   3. Go to Settings to configure API keys"
echo "   4. Upload titles and schedule posts!"
echo ""
echo "📝 App will be available at: https://your-app-name.onrender.com"
