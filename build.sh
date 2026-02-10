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

# Navigate to chatterbox package directory
echo "📦 Installing chatterbox package..."
cd chatterbox

# Install the package properly using pip in editable mode
echo "📦 Installing chatterbox package in editable mode..."
pip install -e . --no-build-isolation

# Verify the package structure
echo "🔍 Checking package structure..."
ls -la src/
ls -la src/chatterbox/

# Verify installation by importing 
echo "✅ Verifying installation..."
python -c "
import sys
print('🐍 Python version:', sys.version)
print('📦 Python path:')
for p in sys.path:
    print('  ', p)

try:
    import chatterbox
    print('✅ Chatterbox package installed and importable')
    print('📍 Package location:', chatterbox.__file__)
    
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
    print('✅ ChatterboxMultilingualTTS import successful')
    print('✅ SUPPORTED_LANGUAGES import successful')
    print('🌍 Supported languages:', len(SUPPORTED_LANGUAGES))
except Exception as e:
    print('❌ Import error:', e)
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo "🚀 Build complete!"