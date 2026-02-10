#!/bin/bash
# Check if EC2 instance has Andrew Tate voice configuration

echo "🔍 Checking if your EC2 instance has Andrew Tate voice..."
echo "=================================================="

read -p "Enter your EC2 API URL (e.g., http://your-ec2-ip:5000): " API_URL

if [[ -z "$API_URL" ]]; then
    echo "❌ No URL provided"
    exit 1
fi

echo ""
echo "1️⃣ Testing API connectivity..."
if curl -s --connect-timeout 5 "$API_URL/health" > /dev/null; then
    echo "✅ API is reachable"
else
    echo "❌ API not reachable - check URL or instance status"
    exit 1
fi

echo ""
echo "2️⃣ Checking available characters..."
CHARACTERS_RESPONSE=$(curl -s "$API_URL/characters" 2>/dev/null)

if echo "$CHARACTERS_RESPONSE" | grep -q "andrew_tate"; then
    echo "✅ Andrew Tate character found!"
    
    echo ""
    echo "3️⃣ Getting Andrew Tate character details..."
    curl -s "$API_URL/characters/andrew_tate" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Name: {data.get(\"name\", \"N/A\")}')
    print(f'   Description: {data.get(\"description\", \"N/A\")}')
    print('✅ Andrew Tate character is properly configured')
except:
    print('❌ Could not parse Andrew Tate character data')
    " 2>/dev/null || echo "❌ Andrew Tate character endpoint not working"

    echo ""
    echo "4️⃣ Testing Andrew Tate voice generation..."
    VOICE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tts" \
        -H "Content-Type: application/json" \
        -d '{
          "text": "Listen up, brother! This is a test of the Andrew Tate voice.",
          "character_id": "andrew_tate",
          "format": "base64",
          "max_tokens": 100
        }' 2>/dev/null)
        
    if echo "$VOICE_RESPONSE" | grep -q '"success":true'; then
        echo "✅ Andrew Tate voice generation working!"
        echo "$VOICE_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Duration: {data.get(\"duration_seconds\", \"N/A\")}s')
    print(f'   Sample Rate: {data.get(\"sample_rate\", \"N/A\")}Hz')
except:
    pass
        " 2>/dev/null
    else
        echo "❌ Andrew Tate voice generation failed"
        echo "Response: $VOICE_RESPONSE" | head -n 3
    fi

else
    echo "❌ Andrew Tate character NOT found"
    echo ""
    echo "📋 Available characters:"
    echo "$CHARACTERS_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for char in data.get('characters', []):
        print(f'   • {char.get(\"id\", \"unknown\")} - {char.get(\"name\", \"Unknown\")}')
except:
    print('   Could not parse characters list')
    " 2>/dev/null
    
    echo ""
    echo "🔄 Your EC2 instance needs to be updated!"
    echo ""
    echo "To update your EC2 instance:"
    echo "1. Run: ./update_ec2.sh"
    echo "2. Or manually SSH and run:"
    echo "   cd chatterbox && git pull && sudo systemctl restart chatterbox-tts"
fi

echo ""
echo "==============================================="
if echo "$CHARACTERS_RESPONSE" | grep -q "andrew_tate"; then
    echo "🎉 STATUS: Your EC2 instance IS UPDATED with Andrew Tate voice!"
    echo "Your Vercel frontend can now use character_id: 'andrew_tate'"
else
    echo "⚠️  STATUS: Your EC2 instance NEEDS UPDATE"
    echo "Run ./update_ec2.sh to deploy Andrew Tate voice"
fi