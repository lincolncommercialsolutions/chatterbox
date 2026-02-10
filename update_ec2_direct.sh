#!/bin/bash
# Direct EC2 Update for Andrew Tate Voice
# Usage: ./update_ec2_direct.sh

EC2_IP="13.220.203.224"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"

echo "🔄 Updating EC2 instance: $EC2_IP"
echo "📋 This will:"
echo "   • Pull latest code with Andrew Tate voice"
echo "   • Upload .env configuration"  
echo "   • Restart the TTS service"
echo "   • Test the update"
echo ""

if [[ ! -f "$SSH_KEY" ]]; then
    echo "❌ SSH key not found at: $SSH_KEY"
    echo "Please ensure your SSH key is available"
    exit 1
fi

echo "📤 Uploading configuration..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no .env ubuntu@"$EC2_IP":/home/ubuntu/chatterbox/.env

echo "🔄 Updating instance code..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@"$EC2_IP" << 'EOF'
set -e

echo "📥 Updating Chatterbox code..."
cd /home/ubuntu/chatterbox
git pull origin main

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing any new dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt --quiet

echo "🔄 Restarting TTS service..."
# Kill any existing processes
pkill -f "api_server.py" || true
pkill -f "python.*api_server" || true

# Wait a moment
sleep 3

# Start the service in background
nohup python chatterbox/api_server.py > /tmp/chatterbox.log 2>&1 &

echo "⏳ Waiting for service to start..."
sleep 10

# Check if process is running
if pgrep -f "api_server.py" > /dev/null; then
    echo "✅ Service started successfully"
else
    echo "❌ Service failed to start"
    echo "📋 Last few log lines:"
    tail -n 10 /tmp/chatterbox.log || echo "No logs available"
    exit 1
fi
EOF

echo ""
echo "🧪 Testing the updated instance..."
sleep 5

# Test health
echo "1️⃣ Health check..."
if curl -s --connect-timeout 10 "http://$EC2_IP:5000/health" | grep -q "healthy"; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
fi

# Test characters
echo ""
echo "2️⃣ Checking characters..."
CHARS_RESPONSE=$(curl -s "http://$EC2_IP:5000/characters" 2>/dev/null)

if echo "$CHARS_RESPONSE" | grep -q "andrew_tate"; then
    echo "✅ Andrew Tate character found!"
    
    # Test Andrew Tate voice
    echo ""
    echo "3️⃣ Testing Andrew Tate voice generation..."
    TEST_RESPONSE=$(curl -s -X POST "http://$EC2_IP:5000/api/v1/tts" \
        -H "Content-Type: application/json" \
        -d '{
          "text": "Listen up, brother! This is Andrew Tate speaking.",
          "character_id": "andrew_tate",
          "format": "base64",
          "max_tokens": 100
        }' 2>/dev/null)
        
    if echo "$TEST_RESPONSE" | grep -q '"success":true'; then
        echo "✅ Andrew Tate voice generation working!"
        echo ""
        echo "🎉 UPDATE COMPLETE!"
        echo "Your Vercel frontend can now use:"
        echo "   Character ID: andrew_tate"
        echo "   API URL: http://$EC2_IP:5000"
    else
        echo "❌ Voice generation test failed"
    fi
else
    echo "❌ Andrew Tate character still not found"
    echo "📋 Available characters:"
    echo "$CHARS_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for char in data.get('characters', []):
        print(f'   • {char.get(\"id\", \"unknown\")} - {char.get(\"name\", \"Unknown\")}')
except:
    print('   Could not parse response')
    " 2>/dev/null
fi