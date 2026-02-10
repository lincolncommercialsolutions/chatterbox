#!/bin/bash
# Deploy Admin Interface to Render

echo "🎛️ Chatterbox Admin Interface Deployment"
echo "========================================"

# Check we're in the right directory
if [ ! -f "chatterbox/api_server.py" ]; then
    echo "❌ Error: Must run from chatterbox project root"
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo "📋 Staging changes..."

# Stage all changes
git add .

echo "💾 Committing changes..."

# Commit changes
git commit -m "✨ Add Admin Interface for Voice & Character Management

- Complete web-based admin panel at /admin
- Upload voice audio files to S3
- Create and manage characters visually
- Test voice generation with live playback
- Delete voices and characters safely
- Real-time parameter tuning
- Automatic configuration persistence
- Full mobile-responsive design"

echo "🚀 Pushing to GitHub..."

# Push to GitHub
git push origin main

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "🌐 Your admin interface will be available at:"
echo "   Local:    http://localhost:5000/admin"
echo "   Render:   https://your-app.onrender.com/admin"
echo ""
echo "📋 Next Steps:"
echo "   1. Wait for Render to auto-deploy (~2-3 minutes)"
echo "   2. Open /admin in your browser" 
echo "   3. Upload voice samples and create characters"
echo "   4. Test everything with live audio playback"
echo ""
echo "📚 Documentation:"
echo "   - Admin Guide: ADMIN_INTERFACE_GUIDE.md"
echo "   - Voice Setup: HOW_TO_ADD_VOICES.md"
echo ""
echo "🎉 Ready to manage your TTS system visually!"