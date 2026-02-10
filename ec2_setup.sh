#!/bin/bash
# Chatterbox TTS EC2 Deployment Script
set -e

echo "🚀 Setting up Chatterbox TTS on EC2 with GPU support..."

# Update system
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip git libsndfile1 ffmpeg curl wget

# Install NVIDIA drivers and CUDA (for GPU instances)
if lspci | grep -i nvidia > /dev/null; then
    echo "📦 Installing NVIDIA drivers and CUDA..."
    
    # Install NVIDIA driver
    sudo apt-get install -y nvidia-driver-525 nvidia-utils-525
    
    # Install CUDA toolkit
    wget https://developer.download.nvidia.com/compute/cuda/12.1.1/local_installers/cuda_12.1.1_530.30.02_linux.run
    sudo sh cuda_12.1.1_530.30.02_linux.run --silent --toolkit
    
    # Add CUDA to PATH
    echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
    source ~/.bashrc
fi

# Clone repository
cd /home/ubuntu
if [ ! -d "chatterbox" ]; then
    git clone https://github.com/lincolncommercialsolutions/chatterbox.git
fi
cd chatterbox

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip

# Install PyTorch with CUDA support
if nvidia-smi > /dev/null 2>&1; then
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install other dependencies
pip install flask flask-cors boto3 python-dotenv werkzeug soundfile numpy

# Install chatterbox package
cd chatterbox
pip install -e .
cd ..

# Copy .env file (make sure .env is uploaded to EC2 first)
if [ -f ".env" ]; then
    echo "✅ Using existing .env file"
else    
    echo "🔧 Creating .env file with default configuration..."
    cp .env.example .env
fi

# Test installation
echo "🧪 Testing installation..."
python -c "
try:
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    print('✅ Chatterbox import successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
"

# Test GPU availability
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU device: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
"

# Create systemd service for auto-start
echo "🔧 Setting up systemd service..."
sudo tee /etc/systemd/system/chatterbox-tts.service > /dev/null << 'EOF'
[Unit]
Description=Chatterbox TTS API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chatterbox
Environment=PATH=/home/ubuntu/chatterbox/venv/bin
ExecStart=/home/ubuntu/chatterbox/venv/bin/python chatterbox/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable chatterbox-tts
sudo systemctl start chatterbox-tts

echo ""
echo "✅ Chatterbox TTS EC2 setup complete!"
echo ""
echo "📋 Service commands:"
echo "  sudo systemctl start chatterbox-tts     - Start the service"
echo "  sudo systemctl stop chatterbox-tts      - Stop the service"
echo "  sudo systemctl restart chatterbox-tts   - Restart the service"
echo "  sudo systemctl status chatterbox-tts    - Check service status"
echo "  sudo journalctl -u chatterbox-tts -f    - View logs"
echo ""
echo "🔗 API will be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000"
echo "🧪 Test with: curl http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5000/health"
