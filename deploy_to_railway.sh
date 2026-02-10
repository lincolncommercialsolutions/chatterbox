#!/bin/bash
set -e

echo "🚂 Railway Deployment Script"
echo "=============================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    
    # Try npm install
    if command -v npm &> /dev/null; then
        echo "Using npm to install Railway CLI..."
        npm install -g @railway/cli
    else
        echo "Installing Railway CLI using curl..."
        bash <(curl -fsSL cli.new)
    fi
    
    echo "✓ Railway CLI installed"
else
    echo "✓ Railway CLI already installed"
    railway --version
fi

echo ""
echo "Next steps:"
echo "1. Login to Railway:"
echo "   railway login"
echo ""
echo "2. Initialize Railway project:"
echo "   cd /home/linkl0n/chatterbox"
echo "   railway init"
echo ""
echo "3. Set environment variables:"
echo "   railway variables set AWS_ACCESS_KEY_ID=your-key"
echo "   railway variables set AWS_SECRET_ACCESS_KEY=your-secret"
echo "   railway variables set AWS_REGION=us-east-1"
echo "   railway variables set S3_ENABLED=true"
echo "   railway variables set S3_BUCKET_NAME=chatterbox-audio-231399652064"
echo "   railway variables set API_PORT=5000"
echo "   railway variables set CORS_ORIGINS=\"*\""
echo ""
echo "4. Deploy:"
echo "   railway up"
echo ""
echo "5. Get your URL:"
echo "   railway open"
echo ""
