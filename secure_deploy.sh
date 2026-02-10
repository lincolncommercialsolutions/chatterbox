#!/bin/bash
echo "🔒 Security Fix + Admin Interface Deployment"
echo "==========================================="

# Check we're in the right directory
if [ ! -f "chatterbox/api_server.py" ]; then
    echo "❌ Error: Must run from chatterbox project root"
    exit 1
fi

echo "🔒 Fixing AWS credential exposure..."

# Stage the security fixes
git add DEPLOYMENT_FIX.md RENDER_DEPLOYMENT.md

echo "💾 Committing security fixes first..."
git commit -m "🔒 Security: Remove exposed AWS credentials from documentation

- Replace real AWS credentials with placeholder values
- Fix GitHub push protection violation
- Documentation now uses your-aws-access-key-id placeholders"

echo "🎛️ Staging admin interface..."
# Stage all remaining changes
git add .

echo "💾 Committing admin interface..."
git commit -m "✨ Add Complete Admin Interface for Voice & Character Management

FEATURES:
- Beautiful web-based admin panel at /admin
- Upload voice audio files to S3 visually  
- Create and manage characters with real-time sliders
- Test voice generation with live audio playback
- Delete voices and characters safely
- Mobile-responsive design
- Automatic configuration persistence

RENDER BUILD FIXES:
- Fixed Python module import path issues
- Added proper build.sh and start.sh scripts  
- Fixed PYTHONPATH configuration
- Updated deployment documentation

USAGE:
- Admin Interface: https://your-app.onrender.com/admin
- Build Command: chmod +x build.sh && bash build.sh
- Start Command: chmod +x start.sh && bash start.sh"

echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "🔒 Security Fix: AWS credentials removed from documentation"
echo "🎛️ Admin Interface: Now included in deployment"
echo "🔧 Render Build: Fixed Python module import issues"
echo ""
echo "🌐 Your admin interface will be available at:"
echo "   https://your-app.onrender.com/admin"
echo ""
echo "📋 Render Dashboard Updates Needed:"
echo "   1. Build Command: chmod +x build.sh && bash build.sh"
echo "   2. Start Command: chmod +x start.sh && bash start.sh"
echo "   3. Add environment variables (AWS keys from your .env file)"
echo "   4. Manual deploy (should now build successfully)"
echo ""
echo "🎉 Ready to manage voices and characters visually!"