#!/bin/bash
# Complete EC2 and S3 Setup and Deployment Script

set -e

echo "🚀 Complete Chatterbox TTS Deployment Setup"
echo "==========================================="

# Get deployment details
read -p "Enter your EC2 instance IP/hostname: " EC2_HOST
read -p "Enter your SSH key path (default: ~/.ssh/id_rsa): " SSH_KEY
SSH_KEY=${SSH_KEY:-~/.ssh/id_rsa}

echo ""
echo "📋 Deployment plan:"
echo "   🔹 Upload configuration files"
echo "   🔹 Set up EC2 instance with GPU support"
echo "   🔹 Install Chatterbox TTS with Andrew Tate voice"
echo "   🔹 Configure systemd service"
echo "   🔹 Test API endpoints"
echo "   🔹 Verify Vercel integration"
echo ""
read -p "Continue with deployment? (y/N): " CONFIRM
if [[ $CONFIRM != "y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "📤 Step 1: Uploading configuration files..."
scp -i "$SSH_KEY" .env ubuntu@"$EC2_HOST":/home/ubuntu/
scp -i "$SSH_KEY" ec2_setup.sh ubuntu@"$EC2_HOST":/home/ubuntu/
echo "✅ Configuration uploaded"

echo ""
echo "🔧 Step 2: Setting up EC2 instance..."
ssh -i "$SSH_KEY" ubuntu@"$EC2_HOST" << 'REMOTE_SETUP'
# Make setup script executable and run it
chmod +x ec2_setup.sh
./ec2_setup.sh
REMOTE_SETUP

echo ""
echo "📥 Step 3: Updating code with Andrew Tate voice..."
ssh -i "$SSH_KEY" ubuntu@"$EC2_HOST" << 'REMOTE_UPDATE'
cd chatterbox
git pull origin main
source venv/bin/activate

# Restart the service with new configuration
sudo systemctl restart chatterbox-tts
sleep 5

# Check service status
sudo systemctl status chatterbox-tts
REMOTE_UPDATE

echo ""
echo "🧪 Step 4: Testing deployment..."
./test_vercel_integration.sh

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📋 Your Chatterbox TTS API is now running on:"
echo "   🔗 URL: http://$EC2_HOST:5000"
echo "   🎭 Characters: 7 available (including Andrew Tate)"
echo "   🗣️ Andrew Tate Voice: Compatible with Vercel frontend"
echo ""
echo "🔧 Useful commands for EC2:"
echo "   ssh -i $SSH_KEY ubuntu@$EC2_HOST"
echo "   sudo systemctl status chatterbox-tts"
echo "   sudo journalctl -u chatterbox-tts -f"
echo ""
echo "📱 For your Vercel frontend:"
echo "   NEXT_PUBLIC_API_URL=http://$EC2_HOST:5000"
echo "   Character ID: 'andrew_tate'"