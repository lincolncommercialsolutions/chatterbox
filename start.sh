#!/bin/bash
echo "🚀 Starting Chatterbox API Server"

# Set up Python path to include both the chatterbox directory and the src directory
export PYTHONPATH="/opt/render/project/src:/opt/render/project/src/chatterbox:/opt/render/project/src/chatterbox/src:${PYTHONPATH}"

# Change to the chatterbox directory where api_server.py is located
cd chatterbox

# Verify package is available
python -c "import chatterbox; print('✅ Chatterbox module loaded')" || {
    echo "❌ Chatterbox module not found, trying to install..."
    pip install -e . --no-build-isolation
    # Add the src directory to Python path
    export PYTHONPATH="$(pwd)/src:${PYTHONPATH}"
    python -c "import chatterbox; print('✅ Chatterbox module loaded after install')"
}

# Start the API server
echo "🌟 Starting API server with admin interface..."
echo "📍 Admin Interface: http://localhost:5000/admin"
python api_server.py