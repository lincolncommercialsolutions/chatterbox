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

# Verify installation by importing from the src directory
echo "✅ Verifying installation..."
export PYTHONPATH="$(pwd)/src:${PYTHONPATH}"
python -c "
import sys
sys.path.insert(0, 'src')
import chatterbox
print('✅ Chatterbox package installed and importable')
print('Package location:', chatterbox.__file__)
"

echo "🚀 Build complete!"