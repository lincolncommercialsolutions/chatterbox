#!/bin/bash
echo "🚀 Starting Chatterbox API Server"

# Set up Python path for Render environment
export PYTHONPATH="/opt/render/project/src/chatterbox/src:/opt/render/project/src:/opt/render/project/src/chatterbox:${PYTHONPATH}"

# Change to the chatterbox directory where api_server.py is located
cd chatterbox

# Verify package and critical imports are available
echo "🔍 Verifying chatterbox module..."
python -c "
import sys
print('🐍 Python path:')
for p in sys.path:
    print('  -', p)
print('\n📦 Testing imports...')
try:
    import chatterbox
    print('✅ chatterbox imported from:', chatterbox.__file__)
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
    print('✅ ChatterboxMultilingualTTS import successful')
    print('✅ SUPPORTED_LANGUAGES import successful')
except Exception as e:
    print('❌ Import error:', e)
    # Try alternative import path
    sys.path.insert(0, 'src')
    import chatterbox
    print('✅ chatterbox imported with alternative path')
" || {
    echo "❌ Critical import failure, attempting fix..."
    # Emergency fallback: try installing package again
    pip install -e . --no-build-isolation
    pip install ./src/ --force-reinstall
    export PYTHONPATH="$(pwd)/src:${PYTHONPATH}"
}

# Set server host and port for Render
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}

# Start the API server
echo "🌟 Starting API server with admin interface..."
echo "📍 Admin Interface will be available at: /admin"
echo "🌐 Server binding to: ${HOST}:${PORT}"
python api_server.py