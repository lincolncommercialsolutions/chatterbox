#!/bin/bash
# Test Andrew Tate voice after EC2 update

echo "🧪 Testing EC2 Update - Andrew Tate Voice"
echo "========================================"

EC2_IP="13.220.203.224"
API_URL="http://$EC2_IP:5000"

echo "Instance: $EC2_IP"
echo "Waiting for instance to be ready..."

# Wait for API to be ready
for i in {1..12}; do
    echo "Attempt $i/12..."
    if curl -s --connect-timeout 10 "$API_URL/health" | grep -q "healthy"; then
        echo "✅ API is healthy!"
        break
    else
        echo "⏳ Still starting up..."
        sleep 15
    fi
done

echo ""
echo "📋 Checking characters..."
RESPONSE=$(curl -s "$API_URL/characters" 2>/dev/null)

if echo "$RESPONSE" | grep -q "andrew_tate"; then
    echo "🎉 SUCCESS! Andrew Tate character is now available!"
    
    echo ""
    echo "📋 All available characters:"
    echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for char in data.get('characters', []):
        print(f'   • {char.get(\"id\", \"unknown\")} - {char.get(\"name\", \"Unknown\")}')
except:
    print('Could not parse response')
    " 2>/dev/null
    
    echo ""
    echo "✅ Your Vercel frontend can now use:"
    echo "   Character ID: 'andrew_tate'"
    echo "   API URL: $API_URL"
    
else
    echo "❌ Andrew Tate character still not found"
    echo "📋 Available characters:"
    echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for char in data.get('characters', []):
        print(f'   • {char.get(\"id\", \"unknown\")} - {char.get(\"name\", \"Unknown\")}')
    print(f'Total: {len(data.get(\"characters\", []))} characters')
except:
    print('Could not parse response')
    " 2>/dev/null
fi