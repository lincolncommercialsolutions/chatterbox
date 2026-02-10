# Chatterbox TTS API - AWS GPU Deployment Guide

Complete guide for deploying Chatterbox on AWS with GPU support and Vercel frontend integration.

## Table of Contents
1. [Quick Start](#quick-start)
2. [AWS Setup](#aws-setup)
3. [Vercel Frontend Integration](#vercel-frontend-integration)
4. [Deployment Options](#deployment-options)
5. [Monitoring and Scaling](#monitoring-and-scaling)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- Docker and Docker Compose installed locally (for testing)
- Vercel frontend URL
- Git

### Local Testing (with GPU if available)

```bash
# Clone and setup
cd /home/linkl0n/chatterbox

# Copy environment template
cp .env.example .env

# Edit .env with your Vercel frontend URL
# Update CORS_ORIGINS with your Vercel domain

# Build and run with Docker Compose
docker-compose up --build

# Test the API
curl http://localhost:5000/health
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world, this is a test.",
    "character": "narrator"
  }'
```

---

## AWS Setup

### 1. Choose Deployment Option

#### Option A: **AWS ECS (Recommended for scalability)**
- Auto-scaling container service
- Managed by AWS
- Load balancing support
- Better for variable traffic

#### Option B: **AWS EC2 with GPU**
- Direct instance management
- Full control
- Single instance deployment
- Good for consistent load

#### Option C: **AWS Lambda** (Not recommended)
- Cold start delays with TTS models
- Memory/time constraints
- Use only for simple endpoints

### 2. Prepare AWS Environment

#### Create ECR Repository
```bash
# Set AWS region
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repository
aws ecr create-repository \
  --repository-name chatterbox-tts \
  --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

#### Build and Push Docker Image
```bash
# Build image with GPU support
docker build -f Dockerfile.gpu -t chatterbox-tts:latest .

# Tag for ECR
docker tag chatterbox-tts:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chatterbox-tts:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chatterbox-tts:latest
```

### 3. Deploy on ECS (Recommended)

#### Create ECS Task Definition
```json
{
  "family": "chatterbox-tts",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "4096",
  "memory": "16384",
  "containerDefinitions": [
    {
      "name": "chatterbox-tts-api",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/chatterbox-tts:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "API_PORT",
          "value": "5000"
        },
        {
          "name": "DEVICE",
          "value": "cuda"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        },
        {
          "name": "CACHE_ENABLED",
          "value": "true"
        },
        {
          "name": "CORS_ORIGINS",
          "value": "https://yourdomain.vercel.app"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatterbox-tts",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3,
        "startPeriod": 120
      }
    }
  ],
  "requiresCompatibilities": ["EC2"],
  "placementConstraints": [
    {
      "type": "memberOf",
      "expression": "attribute:ecs.instance-type =~ g4dn.*"
    }
  ]
}
```

#### Create ECS Service
```bash
aws ecs create-service \
  --cluster chatterbox-cluster \
  --service-name chatterbox-tts-service \
  --task-definition chatterbox-tts:1 \
  --desired-count 1 \
  --launch-type EC2 \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=chatterbox-tts-api,containerPort=5000 \
  --region us-east-1
```

### 4. Setup EC2 GPU Instance (Alternative)

#### Launch GPU Instance
```bash
# Use AWS Console or CLI to launch:
# - Instance type: g4dn.xlarge (1 GPU) or g4dn.12xlarge (4 GPUs)
# - AMI: Ubuntu 22.04 LTS with NVIDIA drivers pre-installed
# - Storage: 100GB+ for model cache
# - Security Group: Allow inbound on port 5000

# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-public-ip

# Install Docker and dependencies
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install NVIDIA Container Runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-runtime

# Restart Docker daemon
sudo systemctl restart docker

# Clone chatterbox repo
git clone https://github.com/your-repo/chatterbox.git
cd chatterbox

# Configure environment
cp .env.example .env
# Edit .env with your settings
nano .env

# Start the API
docker-compose up -d

# Verify it's running
curl http://localhost:5000/health
```

---

## Vercel Frontend Integration

### 1. Update Frontend Configuration

In your Vercel frontend project, configure the TTS API endpoint:

```typescript
// pages/api/tts.ts or similar endpoint
const TTS_API_URL = process.env.NEXT_PUBLIC_TTS_API_URL || 'https://api.yourdomain.com';

export async function generateAudio(text: string, character: string = 'narrator') {
  try {
    const response = await fetch(`${TTS_API_URL}/generate-audio`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        character: character,
        return_format: 'base64'
      })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.success) {
      // Convert base64 to audio blob
      const audioBuffer = Buffer.from(data.audio, 'base64');
      const audioBlob = new Blob([audioBuffer], { type: 'audio/wav' });
      return audioBlob;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('TTS API error:', error);
    throw error;
  }
}
```

### 2. Environment Variables

Add to your Vercel project settings:

```
NEXT_PUBLIC_TTS_API_URL=https://chatterbox-api.your-domain.com
```

### 3. Handle OpenRouter Integration

```typescript
// When receiving OpenRouter response
async function processOpenRouterResponse(message: string, characterId: string) {
  try {
    // Generate audio for the AI response
    const audioBlob = await generateAudio(message, characterId);
    
    // Return message with audio URL
    const audioUrl = URL.createObjectURL(audioBlob);
    
    return {
      text: message,
      audioUrl: audioUrl,
      character: characterId
    };
  } catch (error) {
    console.error('Failed to generate audio:', error);
    // Fallback: return text without audio
    return {
      text: message,
      character: characterId,
      error: 'Audio generation failed'
    };
  }
}
```

---

## Deployment Options

### Option 1: CloudFormation Template

```bash
# Deploy using CloudFormation
aws cloudformation create-stack \
  --stack-name chatterbox-tts-stack \
  --template-body file://cloudformation-template.yaml \
  --parameters \
    ParameterKey=VPCId,ParameterValue=vpc-xxxxx \
    ParameterKey=InstanceType,ParameterValue=g4dn.xlarge \
  --region us-east-1
```

### Option 2: AWS Copilot

```bash
# Initialize Copilot
copilot app init chatterbox

# Create environment
copilot env init --name prod --profile default --default-config

# Create service
copilot svc init --name tts-api --svc-type "Load Balanced Web Service"

# Deploy
copilot svc deploy
```

### Option 3: Terraform

See `terraform/` directory for complete IaC configuration.

---

## Monitoring and Scaling

### CloudWatch Monitoring

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ChatterboxTTS \
  --dashboard-body file://dashboard-config.json
```

### Auto-Scaling Setup

```bash
# Create auto-scaling target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/chatterbox-cluster/chatterbox-tts-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 3

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/chatterbox-cluster/chatterbox-tts-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### Load Balancer Configuration

The ALB automatically distributes traffic across instances:
- Health check interval: 30s
- Healthy threshold: 2
- Unhealthy threshold: 3
- Timeout: 10s

---

## API Endpoints

### Health Check
```bash
GET /health
Response: GPU status, memory, cache info
```

### Generate Audio (OpenRouter Integration)
```bash
POST /generate-audio
{
  "text": "AI response text",
  "character": "narrator",  # optional
  "return_format": "base64" # optional
}

Response:
{
  "success": true,
  "audio": "base64_encoded_wav",
  "sample_rate": 24000,
  "duration": 2.5,
  "generation_time_ms": 1234
}
```

### List Characters
```bash
GET /characters
Response: Available voice profiles
```

---

## Troubleshooting

### Issue: CUDA Out of Memory
**Solution**: Reduce batch size or use smaller model variant
```bash
# Set environment variable
export BATCH_SIZE=1
export DEFAULT_MAX_TOKENS=300
```

### Issue: Slow Audio Generation
**Solution**: 
- Ensure GPU is being used: check health endpoint
- Check CloudWatch logs
- Increase instance size (g4dn.12xlarge)

### Issue: CORS Errors from Vercel
**Solution**: Update CORS_ORIGINS in environment
```bash
CORS_ORIGINS=https://yourdomain.vercel.app,https://www.yourdomain.vercel.app
```

### Issue: Model Download Fails
**Solution**: Pre-warm model cache
```bash
# Run model loading script
python -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; ChatterboxMultilingualTTS.from_pretrained('cuda')"
```

---

## Cost Estimation (AWS)

- **g4dn.xlarge**: ~$0.53/hour ($377/month)
- **g4dn.12xlarge**: ~$4.25/hour ($3,060/month)
- **Data transfer**: $0.09/GB out
- **CloudWatch logs**: $0.50/GB ingested

**Recommended for production**: g4dn.2xlarge with auto-scaling (2-3 instances)

---

## Support and Updates

- Check logs: `docker-compose logs -f`
- AWS console: ECS → Services → chatterbox-tts-service
- CloudWatch Logs: `/ecs/chatterbox-tts`

For issues, check:
1. GPU availability: `nvidia-smi`
2. Model cache: `/app/.cache/torch`
3. Docker logs: `docker logs chatterbox-tts-api`
