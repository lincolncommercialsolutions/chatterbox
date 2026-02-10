#!/bin/bash
echo "🔧 Chatterbox Build Script for Render"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip

# Install root requirements first
if [ -f "requirements.txt" ]; then
    echo "📦 Installing root requirements..."
    pip install -r requirements.txt
fi

# Install the chatterbox package from the chatterbox subdirectory
echo "📦 Installing chatterbox package..."
cd chatterbox

# Install chatterbox package requirements if there are any
pip install -e . --no-build-isolation

# Also install as regular package to ensure it's in site-packages
pip install ./src/

# Verify installation by importing 
echo "✅ Verifying installation..."
python -c "
import sys
print('Python path:', sys.path)
import chatterbox
print('✅ Chatterbox package installed and importable')
print('Package location:', chatterbox.__file__)
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
print('✅ ChatterboxMultilingualTTS import successful')
"

echo "🚀 Build complete!"