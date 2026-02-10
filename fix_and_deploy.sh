#!/bin/bash
# Quick fix for Render deployment + Admin Interface

set -e  # Exit on any error

echo "🔧 Fixing Render Build Issues + Deploying Admin Interface"
echo "======================================================="

# Check we're in the right directory
if [ ! -f "chatterbox/api_server.py" ]; then
    echo "❌ Error: Must run from chatterbox project root"
    exit 1
fi

# Make scripts executable
chmod +x build.sh start.sh deploy_admin.sh test_admin.sh

echo "📋 Staging changes..."
git add .

echo "💾 Committing fixes..."
git commit -m "🔧 Fix Render build + Add Admin Interface

FIXES:
- Fixed Python module import path for Render deployment
- Added proper build.sh and start.sh scripts
- Fixed PYTHONPATH configuration
- Updated build commands in RENDER_DEPLOYMENT.md

NEW ADMIN INTERFACE:
- Complete web-based admin panel at /admin
- Upload voice audio files to S3 visually
- Create and manage characters with sliders
- Test voice generation with live playback
- Delete voices and characters safely
- Real-time parameter tuning
- Automatic configuration persistence
- Mobile-responsive design

DEPLOYMENT:
- Build command: chmod +x build.sh && bash build.sh
- Start command: chmod +x start.sh && bash start.sh
- Admin URL: https://your-app.onrender.com/admin"

echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "🔧 RENDER BUILD FIX:"
echo "   The build errors should now be resolved"
echo "   - Fixed Python module import paths"
echo "   - Updated build and start commands"
echo ""
echo "🎛️ ADMIN INTERFACE:"
echo "   Your admin interface will be available at:"
echo "   https://your-app.onrender.com/admin"
echo ""
echo "📋 In Render Dashboard:"
echo "   1. Go to your service settings"
echo "   2. Update Build Command: chmod +x build.sh && bash build.sh"
echo "   3. Update Start Command: chmod +x start.sh && bash start.sh"
echo "   4. Trigger a manual deploy"
echo "   5. Check logs - should now build successfully!"
echo ""
echo "🎯 Test Admin Interface:"
echo "   1. Wait for deployment (~3 minutes)"
echo "   2. Go to https://your-app.onrender.com/admin"
echo "   3. Upload voice samples, create characters"
echo "   4. Test audio generation live!"
echo ""
echo "🎉 Your TTS system now has a visual admin interface!"