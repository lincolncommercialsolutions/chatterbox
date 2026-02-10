#!/bin/bash
# Quick EC2 Update Script for Andrew Tate Voice

echo "🚀 Updating EC2 instance with Andrew Tate voice..."

# Get EC2 connection details
if [[ -z "$EC2_HOST" ]]; then
    read -p "Enter your EC2 instance IP/hostname: " EC2_HOST
fi

if [[ -z "$SSH_KEY" ]]; then
    read -p "Enter your SSH key path (or press enter for ~/.ssh/id_rsa): " SSH_KEY
    SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}
fi

echo "🔄 Connecting to EC2: ubuntu@$EC2_HOST"

# Transfer .env file to EC2
echo "📤 Uploading .env configuration..."
scp -i "$SSH_KEY" .env ubuntu@"$EC2_HOST":/home/ubuntu/chatterbox/.env

echo "🔄 Updating EC2 code and restarting service..."

ssh -i "$SSH_KEY" ubuntu@"$EC2_HOST" << 'EOF'
# Navigate to chatterbox directory
cd /home/ubuntu/chatterbox

echo "📥 Pulling latest code from GitHub..."
git pull origin main

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing any new dependencies..."
pip install -r requirements.txt

echo "🔄 Restarting the TTS API server..."
# Kill existing server if running
pkill -f "api_server.py" || true

# Start the server in the background
nohup python chatterbox/api_server.py > api_server.log 2>&1 &

echo "✅ API server restarted!"
echo "📋 Server status:"
sleep 2
ps aux | grep api_server.py | grep -v grep

echo "🌐 Testing server health..."
sleep 5
curl -s http://localhost:5000/health | head -n 5

echo "📋 Available characters:"
curl -s http://localhost:5000/characters | python3 -m json.tool | grep -E '"id"|"name"'
EOF

echo "✅ EC2 update complete!"
echo ""
echo "🧪 To test the Andrew Tate voice from your Vercel frontend:"
echo "   Character ID: andrew_tate"
echo "   Character Name: Andrew Tate"
echo ""
echo "🔗 Make sure your Vercel frontend is pointing to:"
echo "   API_URL: http://your-ec2-ip:5000"
echo ""
echo "📝 Next steps:"
echo "   1. Test /characters endpoint from Vercel"
echo "   2. Generate audio with character: 'andrew_tate'"
echo "   3. Verify S3 audio URLs are accessible"