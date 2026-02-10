#!/bin/bash

# Chatterbox TTS Setup Script
# Sets up the complete environment for S3-based TTS deployment

set -e  # Exit on error

echo "=================================================="
echo "Chatterbox TTS - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found Python $PYTHON_VERSION"

if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "  ✓ Python version is 3.10 or higher"
else
    echo "  ✗ Python 3.10+ required"
    exit 1
fi

# Check virtual environment
echo ""
echo "✓ Checking virtual environment..."
if [ -d ".venv" ]; then
    echo "  ✓ Virtual environment exists"
    source .venv/bin/activate
else
    echo "  ✗ Virtual environment not found"
    echo "  Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install dependencies
echo ""
echo "✓ Installing Python dependencies..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

echo "  Installing Flask and AWS support..."
pip install Flask flask-cors boto3 python-dotenv > /dev/null 2>&1

echo "  ✓ All dependencies installed"

# Check .env file
echo ""
echo "✓ Checking configuration..."
if [ -f ".env" ]; then
    echo "  ✓ .env file found"
else
    echo "  Creating .env file from template..."
    cat > .env << 'EOF'
# ============ AWS & S3 Configuration ============
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# S3 Audio Storage
S3_ENABLED=true
S3_BUCKET_NAME=
S3_AUDIO_PREFIX=chatterbox/audio/
S3_VOICES_PREFIX=chatterbox/voices/
S3_PRESIGNED_URL_EXPIRY=3600

# ============ API Server Configuration ============
API_PORT=5000
API_HOST=0.0.0.0
LOG_LEVEL=INFO

# ============ CORS Configuration (for Vercel frontend) ============
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://*.vercel.app,https://*.vercel.sh

# ============ TTS Generation Settings ============
MAX_TEXT_LENGTH=500
DEFAULT_MAX_TOKENS=400
BATCH_SIZE=1
CACHE_ENABLED=true
CACHE_SIZE=100

# ============ OpenRouter Integration ============
OPENROUTER_API_KEY=

# ============ Character Voice Configuration ============
DEFAULT_CHARACTER=assistant
CHARACTER_CONFIG_FILE=character_voices.json
EOF
    echo "  ✓ .env file created - please configure with your AWS credentials"
fi

# Check character configuration
echo ""
echo "✓ Checking character configuration..."
if [ -f "character_voices.json" ]; then
    echo "  ✓ character_voices.json found"
else
    echo "  ✗ character_voices.json not found"
    echo "  This file should be in the project root"
fi

# Verify S3 connection
echo ""
echo "✓ Verifying S3 connection..."
if grep -q "AWS_ACCESS_KEY_ID=" .env && ! grep -q "AWS_ACCESS_KEY_ID=$" .env; then
    echo "  ✓ AWS credentials configured"
    
    # Test S3 connection
    if python3 test_s3_connection.py > /dev/null 2>&1; then
        echo "  ✓ S3 connection successful"
    else
        echo "  ⚠ S3 connection test failed"
        echo "    Run 'python test_s3_connection.py' for details"
    fi
else
    echo "  ⚠ AWS credentials not configured"
    echo "    Please add your credentials to .env:"
    echo "    AWS_ACCESS_KEY_ID=your_key_id"
    echo "    AWS_SECRET_ACCESS_KEY=your_secret_key"
fi

# Summary
echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Configure .env with your AWS credentials"
echo "2. Create S3 bucket: python s3_manager.py create-bucket"
echo "3. Start API server: python chatterbox/api_server.py"
echo "4. Run tests: python integration_test.py"
echo ""
echo "For more information, see S3_DEPLOYMENT_GUIDE.md"
echo ""
