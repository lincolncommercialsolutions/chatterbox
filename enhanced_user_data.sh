#!/bin/bash
# Enhanced User Data Script with Logging for Troubleshooting

# Log everything to help debug
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "$(date): Starting Chatterbox TTS update..."

# Wait for system to be ready
sleep 30

echo "$(date): System ready, updating Chatterbox..."

# Navigate to chatterbox directory
cd /home/ubuntu/chatterbox || {
    echo "$(date): ERROR - Could not find /home/ubuntu/chatterbox directory"
    exit 1
}

echo "$(date): Pulling latest code from GitHub..."
sudo -u ubuntu git pull origin main

echo "$(date): Activating virtual environment..."
sudo -u ubuntu bash -c 'source venv/bin/activate && echo "Virtual environment activated"'

echo "$(date): Stopping existing processes..."
pkill -f "api_server.py" || true
sleep 5

echo "$(date): Starting new API server process..."
sudo -u ubuntu bash -c 'cd /home/ubuntu/chatterbox && source venv/bin/activate && nohup python chatterbox/api_server.py > /tmp/chatterbox.log 2>&1 &'

# Wait and verify the service started
echo "$(date): Waiting 30 seconds for service to start..."
sleep 30

echo "$(date): Checking if service is running..."
if pgrep -f "api_server.py" > /dev/null; then
    echo "$(date): SUCCESS - API server is running"
    
    # Test the API
    sleep 10
    echo "$(date): Testing API response..."
    curl -s http://localhost:5000/health > /tmp/api_test.log 2>&1 || echo "API test failed"
    
else
    echo "$(date): ERROR - API server failed to start"
    echo "$(date): Last 20 lines of API log:"
    tail -n 20 /tmp/chatterbox.log || echo "No API log found"
fi

echo "$(date): User data script completed"