# Chatterbox TTS - AWS GPU Deployment Package

Complete production-ready deployment package for Chatterbox Text-to-Speech API with GPU support on AWS and Vercel frontend integration.

## 📋 What's Included

### Core API
- **`chatterbox/api_server.py`** - Production Flask API with OpenRouter integration
- **GPU-optimized** with CUDA support for fast inference
- **Audio caching** for repeated requests
- **CORS support** for Vercel frontend
- **Health monitoring** with GPU metrics

### Docker & Deployment
- **`Dockerfile.gpu`** - Multi-stage build for AWS GPU instances
- **`docker-compose.yml`** - Production configuration with health checks
- **`.env.example`** - Environment variables template

### Client Libraries
- **`chatterbox/tts_client.py`** - Python client for backend integration
- **`frontend/chatterbox-tts-client.ts`** - TypeScript client for Vercel/Next.js
- Both support error handling, retries, and caching

### Documentation
- **`AWS_DEPLOYMENT_SETUP.md`** - Complete AWS deployment guide
- **`FRONTEND_INTEGRATION.md`** - Frontend integration with examples
- **`DEPLOYMENT_CHECKLIST.md`** - Step-by-step checklist
- **`DEPLOYMENT_README.md`** - This file

### Testing
- **`test_api.py`** - Comprehensive API test suite

## 🚀 Quick Start (Local Testing)

### Prerequisites
- Python 3.11+
- CUDA 12.1 capable GPU (or CPU fallback)
- Docker & Docker Compose
- 50GB+ free disk space (for model cache)

### 1. Setup Local Environment

```bash
cd /home/linkl0n/chatterbox

# Copy environment template
cp .env.example .env

# Edit environment variables (optional)
nano .env
```

### 2. Build and Run with Docker

```bash
# Build the Docker image
docker build -f Dockerfile.gpu -t chatterbox-tts:latest .

# Run with Docker Compose
docker-compose up

# Wait for model to load (5-10 minutes on first run)
# You'll see: "✓ Model loaded successfully"
```

### 3. Test the API

```bash
# In another terminal, test the health endpoint
curl http://localhost:5000/health

# Generate audio for a test message
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world, this is a test",
    "character": "narrator"
  }'

# Get list of available characters
curl http://localhost:5000/characters
```

### 4. Run Test Suite

```bash
# Install test dependencies (if needed)
pip install requests

# Run comprehensive tests
python test_api.py http://localhost:5000 --verbose

# Expected output:
# ✓ PASS: Health Check
# ✓ PASS: Characters Endpoint
# ✓ PASS: Audio Generation
# ...
```

## 🌐 AWS Deployment

### Prerequisites
- AWS Account with appropriate IAM permissions
- AWS CLI configured
- Docker CLI authenticated with ECR

### Recommended AWS Setup

**Instance Type**: `g4dn.xlarge` or `g4dn.2xlarge`
- GPU: 1x NVIDIA T4 (16GB VRAM)
- vCPU: 4
- Memory: 16 GB
- Cost: ~$0.53/hour

### 1. Push to ECR

```bash
# Set variables
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repository
aws ecr create-repository \
  --repository-name chatterbox-tts \
  --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push image
docker build -f Dockerfile.gpu -t chatterbox-tts:latest .
docker tag chatterbox-tts:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chatterbox-tts:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/chatterbox-tts:latest
```

### 2. Deploy on ECS (Easiest for Production)

```bash
# 1. Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/chatterbox-tts --region $AWS_REGION

# 2. Create ECS cluster
aws ecs create-cluster \
  --cluster-name chatterbox-cluster \
  --region $AWS_REGION

# 3. Register task definition (see AWS_DEPLOYMENT_SETUP.md for full JSON)
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION

# 4. Create service
aws ecs create-service \
  --cluster chatterbox-cluster \
  --service-name chatterbox-tts-service \
  --task-definition chatterbox-tts:1 \
  --desired-count 1 \
  --region $AWS_REGION
```

### 3. Deploy on EC2 (Direct Control)

```bash
# SSH into your g4dn instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker and dependencies
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install NVIDIA Container Runtime
sudo apt-get update
sudo apt-get install -y nvidia-container-runtime

# Clone repository
git clone https://github.com/your-repo/chatterbox.git
cd chatterbox

# Configure environment
cp .env.example .env
# Edit .env with your settings
nano .env

# Start the service
docker-compose up -d

# Verify
curl http://localhost:5000/health
```

## 📱 Frontend Integration (Vercel)

### 1. Install TypeScript Client

```bash
# Copy client to your Next.js project
cp frontend/chatterbox-tts-client.ts ./lib/
```

### 2. Setup Environment

Add to `.env.local`:

```env
NEXT_PUBLIC_TTS_API_URL=https://your-api-domain.com
```

### 3. Basic Usage

```typescript
import { ChatterboxTTSClient } from '@/lib/chatterbox-tts-client';

const ttsClient = new ChatterboxTTSClient(
  process.env.NEXT_PUBLIC_TTS_API_URL
);

// Generate audio for OpenRouter response
const audio = await ttsClient.generateAudio({
  text: "AI character response",
  character: "narrator"
});

// Convert to playable URL
const { url, duration, revoke } = await ttsClient.generatePlayableAudio({
  text: "Hello world!",
  character: "friendly"
});

// Use in audio element
<audio src={url} controls autoPlay />
```

### 4. React Hook (Recommended)

```typescript
import { useChatterboxTTS } from '@/lib/chatterbox-tts-client';

export function ChatMessage({ message, character }) {
  const { generateAudio, isLoading, audioUrl } = useChatterboxTTS(
    process.env.NEXT_PUBLIC_TTS_API_URL
  );

  return (
    <div>
      <p>{message}</p>
      <button onClick={() => generateAudio(message, character)}>
        {isLoading ? 'Generating...' : 'Play Audio'}
      </button>
      {audioUrl && <audio src={audioUrl} controls autoPlay />}
    </div>
  );
}
```

See `FRONTEND_INTEGRATION.md` for complete examples.

## 📊 Configuration

### API Environment Variables

```env
# Server
API_PORT=5000
DEVICE=cuda                    # or 'cpu'

# Logging
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR

# Text Processing
MAX_TEXT_LENGTH=500           # Maximum text length
DEFAULT_MAX_TOKENS=400        # Tokens for generation

# Caching
CACHE_ENABLED=true            # Enable audio caching

# CORS (for Vercel frontend)
CORS_ORIGINS=https://yourdomain.vercel.app,https://www.yourdomain.vercel.app

# GPU Configuration
CUDA_VISIBLE_DEVICES=0        # GPU device ID
TORCH_CUDA_ARCH_LIST="7.0;8.0;8.6;9.0"
```

## 🔍 Monitoring & Logs

### CloudWatch Logs (AWS)

```bash
# View logs in real-time
aws logs tail /ecs/chatterbox-tts --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /ecs/chatterbox-tts \
  --filter-pattern ERROR
```

### Local Docker Logs

```bash
# View running container logs
docker-compose logs -f

# View specific service logs
docker logs chatterbox-tts-api -f
```

### Health Monitoring

```bash
# Check API health and GPU status
curl https://your-api-domain.com/health | jq

# Expected response:
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "gpu": {
    "cuda_available": true,
    "device": "Tesla V100",
    "memory_allocated": "4.2GB"
  }
}
```

## 🧪 Testing

### Run Full Test Suite

```bash
# Test local API
python test_api.py http://localhost:5000 --verbose

# Test production API
python test_api.py https://your-api-domain.com

# Test with custom text
python test_api.py http://localhost:5000 <<< "Your test message"
```

### Manual Tests

```bash
# Health check
curl http://localhost:5000/health

# Get characters
curl http://localhost:5000/characters

# Generate audio
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Test message","character":"narrator"}'

# Load test with Apache Bench
ab -n 100 -c 5 http://localhost:5000/health
```

## 🔧 Troubleshooting

### Issue: CUDA Out of Memory
```bash
# Reduce batch size and token count
export BATCH_SIZE=1
export DEFAULT_MAX_TOKENS=300
docker-compose up
```

### Issue: API Not Responding
```bash
# Check if container is running
docker ps | grep chatterbox

# Check logs
docker-compose logs -f

# Restart container
docker-compose restart
```

### Issue: CORS Errors from Frontend
```bash
# Update .env with correct Vercel domain
CORS_ORIGINS=https://yourdomain.vercel.app

# Restart API
docker-compose restart
```

### Issue: Model Download Fails
```bash
# Pre-download model manually
docker run --rm -it \
  -v chatterbox_torch_cache:/app/.cache/torch \
  chatterbox-tts:latest \
  python -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; ChatterboxMultilingualTTS.from_pretrained('cuda')"
```

## 📈 Performance Tips

1. **GPU Instance Selection**
   - Use g4dn.xlarge (1 GPU) for moderate load
   - Use g4dn.2xlarge+ for high load
   - g4dn instances have excellent TTS performance

2. **Caching**
   - Enable `CACHE_ENABLED=true` (default)
   - Repeated requests are 10x faster
   - Cache size: 100 items max

3. **Batch Processing**
   - Generate multiple audios in parallel on frontend
   - Don't send 10+ requests simultaneously
   - Use reasonable stagger (100-200ms between)

4. **Text Length**
   - Shorter text = faster generation
   - Ideal range: 50-300 characters
   - Max supported: 500 characters

5. **Character Selection**
   - All characters use same model
   - Selection affects voice quality, not speed
   - No performance penalty for different voices

## 📚 Documentation Structure

- **`AWS_DEPLOYMENT_SETUP.md`** - Detailed AWS deployment
- **`FRONTEND_INTEGRATION.md`** - Frontend integration guide
- **`DEPLOYMENT_CHECKLIST.md`** - Pre-deployment checklist
- **`api_server.py`** - Inline API documentation
- **`tts_client.py`** - Python client documentation
- **`chatterbox-tts-client.ts`** - TypeScript client documentation

## 🔐 Security Considerations

1. **CORS Configuration**
   - Restrict to specific Vercel domain
   - Never use wildcard in production

2. **API Authentication** (Optional)
   - Add API key validation
   - Use AWS Cognito for user auth

3. **SSL/TLS**
   - Use ACM certificate in AWS
   - Enforce HTTPS in production

4. **Rate Limiting**
   - Implement in ALB or application
   - Default: no limit (add as needed)

## 📞 Support & Contribution

### For Issues
1. Check logs: `docker-compose logs -f`
2. Test health: `curl http://localhost:5000/health`
3. Run test suite: `python test_api.py`

### Common Solutions
- **Slow generation**: Check GPU with health endpoint
- **Memory errors**: Use smaller instances or batch smaller
- **CORS issues**: Verify CORS_ORIGINS in .env
- **Model loading**: Check disk space and internet

## 📝 Next Steps

1. **Immediate**: Test locally with `docker-compose up`
2. **Short-term**: Follow AWS_DEPLOYMENT_SETUP.md for deployment
3. **Integration**: Use FRONTEND_INTEGRATION.md to connect frontend
4. **Production**: Complete DEPLOYMENT_CHECKLIST.md before going live
5. **Monitoring**: Setup CloudWatch alarms and dashboards

## 📋 Files Reference

| File | Purpose |
|------|---------|
| `chatterbox/api_server.py` | Main API application |
| `Dockerfile.gpu` | Docker build configuration |
| `docker-compose.yml` | Local/production deployment |
| `chatterbox/tts_client.py` | Python TTS client library |
| `frontend/chatterbox-tts-client.ts` | TypeScript TTS client |
| `test_api.py` | API test suite |
| `AWS_DEPLOYMENT_SETUP.md` | AWS deployment guide |
| `FRONTEND_INTEGRATION.md` | Frontend integration guide |
| `DEPLOYMENT_CHECKLIST.md` | Pre-deployment checklist |
| `.env.example` | Environment variables template |

---

## 🎯 Deployment Summary

```
Local Testing
    ↓
Build Docker Image
    ↓
Push to ECR
    ↓
Deploy to ECS/EC2
    ↓
Configure Load Balancer
    ↓
Setup Monitoring
    ↓
Integrate Frontend
    ↓
Go to Production
```

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-09  
**Status**: Production Ready ✅

For detailed information on any section, refer to the corresponding documentation file.
