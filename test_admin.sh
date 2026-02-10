#!/bin/bash
# Test Admin Interface Locally

echo "🧪 Testing Chatterbox Admin Interface"
echo "==================================="

# Check if API server is running
echo "🔍 Checking if API server is running..."

# Test health endpoint
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ API server is running"
else
    echo "❌ API server not running. Start with:"
    echo "   cd /home/linkl0n/chatterbox"
    echo "   python chatterbox/api_server.py"
    echo ""
    echo "Or with Docker:"
    echo "   docker-compose up"
    exit 1
fi

echo ""
echo "🔍 Testing admin endpoints..."

# Test admin endpoints
endpoints=(
    "/admin/voices"
    "/admin/characters" 
    "/characters"
    "/voices"
)

for endpoint in "${endpoints[@]}"; do
    if curl -s http://localhost:5000$endpoint > /dev/null; then
        echo "✅ $endpoint - OK"
    else
        echo "❌ $endpoint - Failed"
    fi
done

echo ""
echo "🌐 Opening admin interface..."

# Try to open in browser
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:5000/admin"
elif command -v open > /dev/null; then
    open "http://localhost:5000/admin"
else
    echo "📋 Open manually: http://localhost:5000/admin"
fi

echo ""
echo "✅ Admin Interface URL: http://localhost:5000/admin"
echo ""
echo "🎯 Test Steps:"
echo "   1. Open the URL above in your browser"
echo "   2. Click through all 4 tabs (Voices, Characters, Upload, Create)"
echo "   3. Try uploading a voice sample (3-5 second WAV/MP3)"
echo "   4. Create a character using an existing voice"
echo "   5. Test voice/character audio generation"
echo ""
echo "🔧 Available Features:"
echo "   🎵 Voice Management - View, upload, test, delete voices"
echo "   🤖 Character Management - View, create, test, delete characters"  
echo "   ⬆️ Audio Upload - Drag & drop voice samples to S3"
echo "   ✨ Character Creation - Visual parameter tuning"
echo "   🎛️ Live Testing - Generate and play audio instantly"
echo ""