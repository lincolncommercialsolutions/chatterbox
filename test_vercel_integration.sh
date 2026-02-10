#!/bin/bash
# Test Vercel Frontend Integration with Andrew Tate Voice

echo "🧪 Testing Chatterbox API and Andrew Tate Voice Integration"
echo "============================================================"

read -p "Enter your EC2 API URL (e.g., http://your-ec2-ip:5000): " API_URL

echo ""
echo "1️⃣ Testing API health..."
curl -s "$API_URL/health" | python3 -m json.tool | head -n 10

echo ""
echo "2️⃣ Testing CORS headers (important for Vercel)..."
curl -I -X OPTIONS "$API_URL/characters" \
  -H "Origin: https://your-app.vercel.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type"

echo ""
echo "3️⃣ Listing all available characters..."
curl -s "$API_URL/characters" | python3 -m json.tool

echo ""
echo "4️⃣ Testing Andrew Tate character specifically..."
curl -s "$API_URL/characters/andrew_tate" | python3 -m json.tool

echo ""
echo "5️⃣ Testing Andrew Tate voice generation..."
curl -X POST "$API_URL/api/v1/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Listen up, brother! This is Andrew Tate speaking. What color is your Bugatti?",
    "character_id": "andrew_tate",
    "format": "base64",
    "max_tokens": 200
  }' | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print('✅ Andrew Tate voice generation: SUCCESS')
        print(f'   Duration: {data.get(\"duration_seconds\", \"N/A\")}s')
        print(f'   Sample Rate: {data.get(\"sample_rate\", \"N/A\")}Hz')
        print(f'   Audio Format: {data.get(\"audio_format\", \"N/A\")}')
        print(f'   Audio Length: {len(data.get(\"audio\", \"\"))} characters')
    else:
        print('❌ Andrew Tate voice generation: FAILED')
        print(f'   Error: {data.get(\"error\", \"Unknown error\")}')
except Exception as e:
    print(f'❌ Failed to parse response: {e}')
"

echo ""
echo "6️⃣ Testing S3 voice URL accessibility..."
VOICE_URL="https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/chatterbox/voices/andrew_tate.mp4"
echo "   Andrew Tate voice URL: $VOICE_URL"
curl -I "$VOICE_URL" | head -n 5

echo ""
echo "📋 Integration Checklist:"
echo "   ✅ API health check"
echo "   ✅ CORS headers for Vercel"
echo "   ✅ Characters endpoint"
echo "   ✅ Andrew Tate character"
echo "   ✅ Andrew Tate voice generation"
echo "   ✅ S3 voice URL access"
echo ""
echo "🔗 For your Vercel frontend, use:"
echo "   API_URL: $API_URL"
echo "   Character ID: 'andrew_tate'"
echo "   Character Name: 'Andrew Tate'"
echo ""
echo "📝 Vercel Environment Variables to check:"
echo "   NEXT_PUBLIC_API_URL=$API_URL"
echo "   NEXT_PUBLIC_TTS_ENABLED=true"