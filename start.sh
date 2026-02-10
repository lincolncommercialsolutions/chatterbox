#!/bin/bash
echo "🚀 Starting Chatterbox API Server"

# Change to the chatterbox directory where api_server.py is located
cd chatterbox

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
    src_path = os.path.join(os.getcwd(), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f'📁 Added to Python path: {src_path}')
    
    try:
        import chatterbox
        print('✅ chatterbox imported with emergency path')
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
        print('✅ Emergency import successful')
    except Exception as e2:
        print('❌ Emergency fallback also failed:', e2)
        sys.exit(1)
"

# Set server host and port for Render
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}

# Start the API server
echo "🌟 Starting API server with admin interface..."
echo "📍 Admin Interface will be available at: /admin"
echo "🌐 Server binding to: ${HOST}:${PORT}"
python api_server.py