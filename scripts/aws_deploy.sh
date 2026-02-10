#!/bin/bash

# AWS Deployment Script for Chatterbox TTS
# This script automates the deployment of Chatterbox to AWS

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
REPOSITORY_NAME="chatterbox-tts"
IMAGE_TAG="latest"
INSTANCE_TYPE="${INSTANCE_TYPE:-g4dn.xlarge}"
KEY_PAIR_NAME="${KEY_PAIR_NAME:-}"
SECURITY_GROUP_ID="${SECURITY_GROUP_ID:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Install it first."
        exit 1
    fi
    
    print_info "Prerequisites check passed"
}

# Get AWS Account ID
get_account_id() {
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        print_info "AWS Account ID: $AWS_ACCOUNT_ID"
    fi
}

# Create ECR repository
create_ecr_repository() {
    print_info "Creating ECR repository..."
    
    if aws ecr describe-repositories \
        --repository-names "$REPOSITORY_NAME" \
        --region "$AWS_REGION" &> /dev/null; then
        print_warning "Repository already exists"
    else
        aws ecr create-repository \
            --repository-name "$REPOSITORY_NAME" \
            --region "$AWS_REGION" \
            --encryption-configuration encryptionType=AES
        print_info "ECR repository created"
    fi
}

# Build Docker image
build_docker_image() {
    print_info "Building Docker image..."
    
    docker build \
        -f Dockerfile.gpu \
        -t "${REPOSITORY_NAME}:${IMAGE_TAG}" \
        -t "${REPOSITORY_NAME}:$(date +%s)" \
        .
    
    print_info "Docker image built successfully"
}

# Push to ECR
push_to_ecr() {
    print_info "Pushing image to ECR..."
    
    # Get login token
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    # Tag image
    docker tag "${REPOSITORY_NAME}:${IMAGE_TAG}" \
        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}"
    
    docker tag "${REPOSITORY_NAME}:${IMAGE_TAG}" \
        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}:latest"
    
    # Push
    docker push "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}"
    docker push "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}:latest"
    
    print_info "Image pushed to ECR successfully"
}

# Launch EC2 instance
launch_ec2_instance() {
    print_info "Launching EC2 instance..."
    
    if [ -z "$KEY_PAIR_NAME" ]; then
        print_error "KEY_PAIR_NAME not set. Please provide your EC2 key pair name."
        exit 1
    fi
    
    if [ -z "$SECURITY_GROUP_ID" ]; then
        print_error "SECURITY_GROUP_ID not set. Please provide your security group ID."
        exit 1
    fi
    
    # Get Ubuntu 22.04 LTS AMI
    AMI_ID=$(aws ec2 describe-images \
        --owners 099720109477 \
        --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
        --region "$AWS_REGION" \
        --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
        --output text)
    
    print_info "Using AMI: $AMI_ID"
    
    # User data script
    read -r -d '' USER_DATA << 'EOF' || true
#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install NVIDIA Docker Runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  tee /etc/apt/sources.list.d/nvidia-docker.list

apt-get update && apt-get install -y nvidia-docker2
systemctl restart docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Nginx
apt-get install -y nginx

# Create app directory
mkdir -p /app/chatterbox
cd /app/chatterbox

# Setup application (you'll need to push code separately or clone from repo)
echo "Chatterbox setup complete. Pull images and start services."
EOF
    
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id "$AMI_ID" \
        --instance-type "$INSTANCE_TYPE" \
        --key-name "$KEY_PAIR_NAME" \
        --security-group-ids "$SECURITY_GROUP_ID" \
        --block-device-mappings DeviceName=/dev/sda1,Ebs="{VolumeSize=100,VolumeType=gp3}" \
        --user-data "$USER_DATA" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=chatterbox-tts-api}]" \
        --region "$AWS_REGION" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    print_info "Instance launched: $INSTANCE_ID"
    
    # Wait for instance to be running
    print_info "Waiting for instance to be running..."
    aws ec2 wait instance-running \
        --instance-ids "$INSTANCE_ID" \
        --region "$AWS_REGION"
    
    # Get public IP
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$AWS_REGION" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    print_info "Instance is running at: $PUBLIC_IP"
    print_info "You can SSH with: ssh -i your-key.pem ubuntu@$PUBLIC_IP"
}

# Create CloudWatch log group
create_log_group() {
    print_info "Creating CloudWatch log group..."
    
    if aws logs describe-log-groups \
        --log-group-name-prefix "/chatterbox/api" \
        --region "$AWS_REGION" &> /dev/null; then
        print_warning "Log group already exists"
    else
        aws logs create-log-group \
            --log-group-name "/chatterbox/api" \
            --region "$AWS_REGION"
        print_info "Log group created"
    fi
}

# Main
main() {
    print_info "Starting Chatterbox AWS Deployment"
    print_info "Region: $AWS_REGION"
    
    check_prerequisites
    get_account_id
    create_ecr_repository
    build_docker_image
    push_to_ecr
    create_log_group
    
    if [ "$LAUNCH_INSTANCE" = "true" ]; then
        launch_ec2_instance
    else
        print_info "Skipping EC2 instance launch. Set LAUNCH_INSTANCE=true to launch."
    fi
    
    print_info "=== Deployment Complete ==="
    print_info "ECR Repository: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}"
    print_info "Image URL: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}"
}

main
