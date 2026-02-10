#!/bin/bash
# Alternative EC2 Update Methods (No SSH Key Required)

echo "🚀 EC2 Update Without SSH Key"
echo "============================="
echo ""
echo "Your instance: 13.220.203.224"
echo "Current status: Missing Andrew Tate voice"
echo ""

# Method 1: Try AWS Session Manager
echo "1️⃣ Trying AWS Systems Manager Session Manager..."
if command -v aws &> /dev/null; then
    # Get instance ID from IP
    INSTANCE_ID=$(aws ec2 describe-instances \
        --filters "Name=private-ip-address,Values=13.220.203.224" \
        --query "Reservations[].Instances[].InstanceId" \
        --output text --region us-east-1 2>/dev/null || \
    aws ec2 describe-instances \
        --filters "Name=ip-address,Values=13.220.203.224" \
        --query "Reservations[].Instances[].InstanceId" \
        --output text --region us-east-1 2>/dev/null)
    
    if [[ -n "$INSTANCE_ID" && "$INSTANCE_ID" != "None" ]]; then
        echo "   Instance ID: $INSTANCE_ID"
        
        # Check if SSM agent is available
        if aws ssm describe-instance-information \
            --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
            --region us-east-1 &>/dev/null; then
            
            echo "   ✅ Session Manager available!"
            echo ""
            echo "   Run this to connect:"
            echo "   aws ssm start-session --target $INSTANCE_ID --region us-east-1"
            echo ""
            echo "   Then run these commands in the session:"
            echo "   cd /home/ubuntu/chatterbox"
            echo "   git pull origin main"
            echo "   sudo systemctl restart chatterbox-tts"
            
        else
            echo "   ❌ Session Manager not available"
        fi
    else
        echo "   ❌ Could not find instance ID"
    fi
else
    echo "   ❌ AWS CLI not available"
fi

echo ""
echo "2️⃣ Alternative Methods:"
echo ""

# Method 2: User Data Script
echo "📋 Option 2A: AWS Console User Data"
echo "   1. Go to AWS EC2 Console"
echo "   2. Find instance 13.220.203.224"
echo "   3. Stop instance → Actions → Instance Settings → Edit User Data"
echo "   4. Add this script:"
echo ""
cat << 'USERDATA'
#!/bin/bash
cd /home/ubuntu/chatterbox
git pull origin main
source venv/bin/activate
pkill -f "api_server.py" || true
sleep 3
nohup python chatterbox/api_server.py > /tmp/chatterbox.log 2>&1 &
USERDATA

echo ""
echo "📋 Option 2B: Create New SSH Key Pair"
echo "   1. Go to AWS EC2 Console → Key Pairs"
echo "   2. Create new key pair"
echo "   3. Stop your instance"
echo "   4. Change key pair (if supported) or create new instance"
echo ""

# Method 3: Direct approach
echo "📋 Option 2C: Terminal Access (If you have it)"
echo "   How do you normally access your EC2 instance?"
echo "   - AWS CloudShell?"
echo "   - EC2 Instance Connect?"
echo "   - Some other terminal?"

echo ""
echo "3️⃣ Quick Test - User Data Approach:"
echo ""
echo "If you want to try the User Data method:"
echo "1. Stop instance 13.220.203.224"
echo "2. Add the user data script above"
echo "3. Start instance"
echo "4. Wait 2-3 minutes and test: curl http://13.220.203.224:5000/characters"
echo ""

# Test current API state
echo "🧪 Current API Status:"
if curl -s --connect-timeout 5 "http://13.220.203.224:5000/health" | grep -q "healthy"; then
    echo "✅ API is running but needs Andrew Tate update"
else
    echo "❌ API not responding"
fi