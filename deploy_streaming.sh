#!/bin/bash
# Deploy Streaming TTS to EC2
# This script pulls the latest code and restarts the service

set -e

EC2_HOST="ubuntu@35.174.4.196"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"  # Override with SSH_KEY env var if needed

echo "🚀 Deploying streaming TTS to EC2..."
echo "   Using SSH key: $SSH_KEY"
echo "   Target: $EC2_HOST"
echo ""

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found: $SSH_KEY"
    echo ""
    echo "Please set the SSH_KEY environment variable:"
    echo "  export SSH_KEY=/path/to/your/key.pem"
    echo "  ./deploy_streaming.sh"
    exit 1
fi

# Deploy
ssh -i "$SSH_KEY" "$EC2_HOST" 'bash -s' << 'ENDSSH'
    set -e
    
    echo "📥 Pulling latest code..."
    cd /home/ubuntu/chatterbox
    git pull
    
    echo "🔄 Restarting chatterbox service..."
    sudo systemctl restart chatterbox
    
    echo "⏳ Waiting for service to start..."
    sleep 3
    
    echo "✅ Checking service status..."
    sudo systemctl status chatterbox --no-pager | head -15
    
    echo ""
    echo "📊 Testing streaming endpoints..."
    
    # Test health
    curl -s http://localhost:5000/health | python3 -m json.tool || echo "Health check failed"
    
    echo ""
    echo "🎵 Testing streaming preview..."
    curl -s -X POST http://localhost:5000/tts-stream-preview \
        -H "Content-Type: application/json" \
        -d '{"text": "Hello world. This is a test.", "max_chunk_chars": 50}' \
        | python3 -m json.tool || echo "Preview endpoint not available"
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test streaming TTS:"
echo "  curl -X POST http://35.174.4.196:5000/tts-stream-preview \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"text\": \"Your text here\", \"max_chunk_chars\": 150}'"
echo ""
echo "Full streaming test:"
echo "  curl -N -X POST http://35.174.4.196:5000/tts-stream \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"text\": \"Hello world. Test streaming.\", \"character\": \"andrew_tate\"}'"
