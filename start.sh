#!/bin/bash
echo "🚀 Starting Chatterbox API Server"

# Record environment information
echo "🔍 Environment info:"
echo "  Working directory: $(pwd)"
echo "  Python: $(which python)"
echo "  HOME: $HOME"
echo "  PORT: ${PORT:-5000}"

# Check if we need to navigate to the chatterbox directory
if [ -f "chatterbox/api_server.py" ]; then
    echo "📍 Found api_server.py in chatterbox/ subdirectory"
    cd chatterbox
elif [ -f "api_server.py" ]; then
    echo "📍 Found api_server.py in current directory"
else
    echo "❌ api_server.py not found!"
    echo "  Directory contents:"
    ls -la
    exit 1
fi

# Verify package and critical imports are available
echo "🔍 Verifying chatterbox module..."
python -c "
import sys
import os
print('🐍 Python version:', sys.version)
print('📂 Current directory:', os.getcwd())
print('🐍 Python path:')
for p in sys.path:
    print('  -', p)

# Add Render-specific paths that might be needed
render_paths = [
    os.path.join(os.getcwd(), 'src'),
    os.path.join(os.path.dirname(os.getcwd()), 'chatterbox', 'src'),
    '/opt/render/project/src/chatterbox/src',
    '/opt/render/project/src'
]

for path in render_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        print(f'📁 Added to Python path: {path}')

print('\n📦 Testing imports...')
try:
    import chatterbox
    print('✅ chatterbox imported from:', chatterbox.__file__)
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
    print('✅ ChatterboxMultilingualTTS import successful')
    print('✅ SUPPORTED_LANGUAGES import successful')
    print('🌍 Supported languages:', len(SUPPORTED_LANGUAGES))
except Exception as e:
    print('❌ Import error:', e)
    import traceback
    traceback.print_exc()
    
    # Emergency fallback: Add src to path and try again
    print('🔧 Attempting emergency fallback...')
    
    # Try multiple potential src locations
    potential_paths = [
        os.path.join(os.getcwd(), 'src'),
        os.path.join(os.path.dirname(os.getcwd()), 'src'),
        '/opt/render/project/src'
    ]
    
    for path in potential_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
            print(f'📁 Emergency path added: {path}')
    
    try:
        import chatterbox
        print('✅ chatterbox imported with emergency path')
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
        print('✅ Emergency import successful')
    except Exception as e2:
        print('❌ Emergency fallback also failed:', e2)
        print('🔍 Available directories:')
        for root, dirs, files in os.walk('.'):
            if 'chatterbox' in dirs or '__init__.py' in files:
                print(f'  Found: {root}')
        sys.exit(1)
"

# Set server host and port for Render
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}

echo "🌟 Starting API server with admin interface..."
echo "📍 Admin Interface will be available at: /admin"
echo "🌐 Server binding to: $HOST:$PORT"

# Start the server
python api_server.py

# Start the API server
echo "🌟 Starting API server with admin interface..."
echo "📍 Admin Interface will be available at: /admin"
echo "🌐 Server binding to: ${HOST}:${PORT}"
python api_server.py