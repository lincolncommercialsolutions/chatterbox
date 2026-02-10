#!/bin/bash
echo "🔧 Chatterbox Build Script for Render"

# Record initial working directory and environment info
echo "📍 Build environment:"
echo "  Working directory: $(pwd)"
echo "  Python: $(which python)"
echo "  Pip: $(which pip)"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip

# Install root requirements first
if [ -f "requirements.txt" ]; then
    echo "📦 Installing root requirements..."
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found in $(pwd)"
    exit 1
fi

# Check for chatterbox package directory
echo "🔍 Checking for chatterbox package..."
if [ ! -d "chatterbox" ]; then
    echo "❌ chatterbox directory not found in $(pwd)"
    echo "Directory contents:"
    ls -la
    exit 1
fi

echo "📦 Installing chatterbox package..."
cd chatterbox

# Verify we have the package structure
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found in $(pwd)"
    echo "Chatterbox directory contents:"
    ls -la
    exit 1
fi

# Also ensure src directory exists
if [ ! -d "src" ]; then
    echo "❌ src directory not found in chatterbox package"
    echo "Contents:"
    ls -la
    exit 1
fi

# Install the package properly using pip in editable mode  
echo "📦 Installing chatterbox package in editable mode..."
# Try installation with different strategies for robustness
pip install -e . --no-build-isolation -v || {
    echo "⚠️ Editable install failed, trying alternative approach..."
    # Alternative: Install without editable mode first, then as editable
    pip install . && pip install -e . --no-build-isolation --force-reinstall
}

# Verify the package structure
echo "🔍 Checking package structure..."
if [ -d "src" ]; then
    ls -la src/
    if [ -d "src/chatterbox" ]; then
        ls -la src/chatterbox/
    else
        echo "❌ src/chatterbox directory not found"
        exit 1
    fi
else
    echo "❌ src directory not found"
    exit 1
fi

# Go back to root for verification
cd ..

# Verify installation by importing 
echo "✅ Verifying installation..."
python -c "
import sys
import os
print('🐍 Python version:', sys.version)
print('📂 Working directory:', os.getcwd())
print('📦 Python path:')
for p in sys.path:
    print('  ', p)

# Add emergency paths to handle Render quirks
src_path = os.path.join(os.getcwd(), 'chatterbox', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f'📁 Emergency path added: {src_path}')

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
    
    # Try to provide helpful debugging info
    print('\n🔍 Debugging info:')
    print('  Current directory:', os.getcwd())
    print('  Directory contents:')
    for item in os.listdir('.'):
        print(f'    {item}')
    if os.path.exists('chatterbox'):
        print('  Chatterbox directory contents:')
        for item in os.listdir('chatterbox'):
            print(f'    chatterbox/{item}')
    sys.exit(1)
"

echo "🚀 Build complete!"

echo "🚀 Build complete!"