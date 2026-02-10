# Chatterbox TTS - AWS GPU Deployment Guide

This guide covers deploying Chatterbox TTS on AWS EC2 with GPU support for integration with your Vercel chatbot frontend.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [EC2 Instance Setup](#ec2-instance-setup)
3. [Docker Deployment](#docker-deployment)
4. [AWS Integration](#aws-integration)
5. [Monitoring and Scaling](#monitoring-and-scaling)
6. [Cost Optimization](#cost-optimization)

## Prerequisites

### AWS Account Requirements
- AWS Account with appropriate IAM permissions
- Access to EC2, ECS, or AppRunner services
- CloudWatch access for monitoring
- ECR (Elastic Container Registry) for storing Docker images

### Recommended AWS Resources
- **EC2 Instance Type**: `g4dn.xlarge` or `g4dn.2xlarge` (recommended for production)
  - GPU: NVIDIA T4 (1 or 2)
  - vCPU: 4-8
  - Memory: 16-32 GB
  - Estimated Cost: $0.526-$1.052/hour (on-demand)

- **Alternative Options**:
  - `g3s.xlarge` - NVIDIA Tesla M60 (cheaper, good for TTS)
  - `g4dn.12xlarge` - Multiple T4s (for high throughput)
  - Spot Instances - Save up to 70% on compute cost

### Software Requirements
- Docker & Docker Compose
- AWS CLI v2
- Git
- Python 3.11+ (for local testing)

## EC2 Instance Setup

### Step 1: Launch EC2 Instance with GPU

```bash
# Using AWS CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \  # Ubuntu 22.04 LTS in us-east-1
  --instance-type g4dn.xlarge \
  --key-name your-key-pair \
  --security-groups sg-xxxxxxxx \
  --iam-instance-profile Name=chatterbox-ec2-role \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=chatterbox-tts-api}]'
```

### Step 2: Configure Security Group

```bash
# Allow HTTP/HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Allow custom port 5000 for API
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxx \
  --protocol tcp --port 5000 --cidr 0.0.0.0/0

# Optional: Restrict to specific IP ranges
# --cidr your-vercel-ip/32
```

### Step 3: Install Dependencies on EC2

```bash
#!/bin/bash
# SSH into your instance first
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install NVIDIA Docker Runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Docker Deployment

### Step 1: Build and Push Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name chatterbox-tts

# Get ECR login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build image (on your machine or EC2)
docker build -f Dockerfile.gpu -t chatterbox-tts:latest .

# Tag for ECR
docker tag chatterbox-tts:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/chatterbox-tts:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/chatterbox-tts:latest
```

### Step 2: Run with Docker Compose on EC2

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Clone repository
git clone https://github.com/your-username/chatterbox.git
cd chatterbox

# Create environment file
cat > .env.production << EOF
CUDA_VISIBLE_DEVICES=0
TORCH_HOME=/app/.cache
HF_HOME=/app/.cache/huggingface
FLASK_ENV=production
EOF

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f chatterbox-tts

# Verify health
curl http://localhost:5000/health
```

### Step 3: Production Server Setup (Gunicorn + Nginx)

```bash
# Install Nginx
sudo apt-get install nginx -y

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/chatterbox << EOF
upstream chatterbox_api {
    server localhost:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # CORS headers
    add_header 'Access-Control-Allow-Origin' 'https://*.vercel.app' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;

    location / {
        proxy_pass http://chatterbox_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts for long generation
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://chatterbox_api;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/chatterbox /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Use Let's Encrypt for SSL (optional)
sudo apt-get install certbot python3-certbot-nginx -y
sudo certbot certonly --nginx -d your-domain.com
```

### Step 4: Systemd Service for Auto-restart

```bash
# Create service file
sudo tee /etc/systemd/system/chatterbox-tts.service << EOF
[Unit]
Description=Chatterbox TTS API Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/chatterbox
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=unless-stopped
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable chatterbox-tts
sudo systemctl start chatterbox-tts
```

## AWS Integration

### Option 1: Direct EC2 Deployment (Recommended for Simplicity)

Use the EC2 instance directly with a public IP or Elastic IP:

```
Vercel Frontend → https://your-api-domain.com → Nginx → Gunicorn → Flask App → GPU
```

### Option 2: AWS App Runner (Serverless Container)

```bash
# Create App Runner service using AWS CLI
aws apprunner create-service \
  --service-name chatterbox-tts \
  --source-configuration ImageRepository='{ImageRepositoryType=ECR,ImageIdentifier=YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/chatterbox-tts:latest,RepositoryCredentialsProviderArn=arn:aws:iam::YOUR_ACCOUNT_ID:role/ecsTaskExecutionRole}' \
  --instance-configuration CpuUnits=4096,Memory=8192 \
  --network-configuration EgressConfiguration='{EgressType=PUBLIC}'
```

### Option 3: ECS with Fargate (More Control)

Create task definition:

```json
{
  "family": "chatterbox-tts",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["EC2"],
  "containerDefinitions": [
    {
      "name": "chatterbox-tts",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/chatterbox-tts:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000,
          "protocol": "tcp"
        }
      ],
      "memory": 8192,
      "cpu": 4096,
      "essential": true,
      "resourceRequirements": [
        {
          "type": "GPU",
          "value": "1"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatterbox-tts",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## Monitoring and Scaling

### CloudWatch Monitoring

```bash
# Create custom metrics from container logs
aws logs create-log-group --log-group-name /chatterbox/api
aws logs create-log-stream --log-group-name /chatterbox/api --log-stream-name production

# Create alarms
aws cloudwatch put-metric-alarm \
  --alarm-name chatterbox-high-requests \
  --alarm-description "Alert when active requests are high" \
  --metric-name ActiveRequests \
  --namespace Chatterbox \
  --statistic Average \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:alert-topic
```

### Load Balancing

For multiple instances:

```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name chatterbox-tts-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --tags Key=Name,Value=chatterbox-alb

# Create target group
aws elbv2 create-target-group \
  --name chatterbox-tts-targets \
  --protocol HTTP \
  --port 5000 \
  --vpc-id vpc-xxxxx \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

### Auto-scaling

```bash
# Create Auto Scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name chatterbox-tts-asg \
  --launch-configuration chatterbox-tts-lc \
  --min-size 1 \
  --max-size 5 \
  --desired-capacity 2 \
  --target-group-arns arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID:targetgroup/chatterbox-tts-targets/xxxxx \
  --vpc-zone-identifier "subnet-xxxxx,subnet-yyyyy"

# Add scaling policy
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name chatterbox-tts-asg \
  --policy-name scale-up \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration 'TargetValue=70,PredefinedMetricSpecification={PredefinedMetricType=ASGAverageCPUUtilization}'
```

## Cost Optimization

### Strategies to Reduce Costs

1. **Use Spot Instances**: Save up to 70% on compute
   ```bash
   # When launching, use --instance-market-options with spot pricing
   ```

2. **GPU Sharing**: Use smaller GPU instances or time-sharing
   - g3s.xlarge: M60 GPU (~cheaper)
   - g4dn.xlarge: Single T4 (good balance)

3. **Reserved Instances**: 
   - 1-year RI: ~30% savings
   - 3-year RI: ~50% savings

4. **Model Caching**: Cache downloaded models in EBS or S3

5. **Request Batching**: Use the `/api/v1/tts-batch` endpoint

### Estimated Monthly Costs (us-east-1, on-demand)

| Instance | CPU Cost | GPU Cost | EBS | Total Monthly |
|----------|----------|----------|-----|---|
| g4dn.xlarge (1x T4) | $0.526 * 730h | = $384 | $30 | ~$414 |
| g4dn.2xlarge (1x T4) | $0.745 * 730h | = $544 | $40 | ~$584 |
| g3s.xlarge (1x M60) | $0.75 * 730h | = $548 | $30 | ~$578 |

*Note: Add data transfer costs (~$0.09/GB egress to internet)*

### Cost Reduction Formula

- **Spot Instance**: ~30% of on-demand cost
- **3-year Reserved**: ~50% of on-demand cost
- **Spot + Reserved Combination**: Even lower with advanced booking

## Troubleshooting

### GPU Not Available

```bash
# Check GPU availability
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all chatterbox-tts nvidia-smi

# If not working, reinstall nvidia-docker2
sudo apt-get remove nvidia-docker2
sudo apt-get install nvidia-docker2
sudo systemctl restart docker
```

### Memory Issues

```bash
# Monitor memory usage
docker stats chatterbox-tts

# Increase swap space if needed
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Model Download Issues

```bash
# Pre-download models
docker run -it --gpus all \
  -v chatterbox_cache:/app/.cache \
  chatterbox-tts python -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; ChatterboxMultilingualTTS.from_pretrained('cuda')"
```

## Security Recommendations

1. **Use HTTPS/TLS**: Always use SSL certificates
2. **API Authentication**: Consider adding API keys for rate limiting
3. **VPC Configuration**: Run in private VPC with NAT gateway
4. **Security Groups**: Restrict to specific IP ranges
5. **IAM Roles**: Use least-privilege IAM policies
6. **Secrets Management**: Use AWS Secrets Manager for credentials

## Next Steps

1. Deploy on EC2 following the guide above
2. Set up monitoring and alerts in CloudWatch
3. Configure your Vercel frontend to use the API endpoint
4. Test thoroughly with production data
5. Implement auto-scaling if needed
6. Set up backup and disaster recovery

## Support

For issues or questions:
- Check CloudWatch logs
- Review application logs: `docker-compose logs -f`
- Verify GPU health: `nvidia-smi`
- Test API endpoints manually with curl
