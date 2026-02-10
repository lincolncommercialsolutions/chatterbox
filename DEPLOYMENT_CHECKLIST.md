# Deployment Checklist - Chatterbox TTS on AWS

Quick reference checklist for deploying Chatterbox TTS API to AWS with GPU support.

## Pre-Deployment

- [ ] AWS Account created and configured
- [ ] Local testing completed successfully
- [ ] Docker image built and tested locally
- [ ] Vercel frontend URL finalized
- [ ] Character voice profiles configured
- [ ] API key/secrets prepared (if using S3, etc)

## Environment Configuration

### `.env` File
- [ ] `API_PORT` set (default: 5000)
- [ ] `DEVICE` set to `cuda`
- [ ] `LOG_LEVEL` configured (INFO for production)
- [ ] `CORS_ORIGINS` includes your Vercel domain
- [ ] `CACHE_ENABLED` set appropriately
- [ ] `MAX_TEXT_LENGTH` set (default: 500)
- [ ] `DEFAULT_MAX_TOKENS` configured (default: 400)

Example:
```bash
API_PORT=5000
DEVICE=cuda
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.vercel.app
CACHE_ENABLED=true
MAX_TEXT_LENGTH=500
DEFAULT_MAX_TOKENS=400
```

## Docker Setup

- [ ] `Dockerfile.gpu` reviewed and updated
- [ ] Docker image builds successfully:
  ```bash
  docker build -f Dockerfile.gpu -t chatterbox-tts:latest .
  ```
- [ ] Image tested locally:
  ```bash
  docker-compose up
  curl http://localhost:5000/health
  ```
- [ ] Image size checked (should be < 15GB)
- [ ] GPU support verified in container:
  ```bash
  docker run --gpus all nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 nvidia-smi
  ```

## AWS Setup

### IAM Permissions
- [ ] IAM user/role created with permissions for:
  - [ ] ECR (create, push images)
  - [ ] ECS (create services, tasks, clusters)
  - [ ] EC2 (launch instances)
  - [ ] CloudWatch (logs)
  - [ ] IAM (assume roles)

### ECR Repository
- [ ] ECR repository created:
  ```bash
  aws ecr create-repository --repository-name chatterbox-tts
  ```
- [ ] Repository policy configured
- [ ] Login token obtained:
  ```bash
  aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com
  ```
- [ ] Image pushed:
  ```bash
  docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/chatterbox-tts:latest
  ```

### VPC Setup
- [ ] VPC created or existing VPC selected
- [ ] Subnets configured (at least 2 for HA)
- [ ] Internet Gateway attached
- [ ] Route tables configured
- [ ] Security group created with rules:
  - [ ] Inbound: Port 5000 (API)
  - [ ] Inbound: Port 22 (SSH, if needed)
  - [ ] Outbound: All (for package downloads)

### Security Group Rules
```
Inbound:
- Type: Custom TCP, Port: 5000, Source: 0.0.0.0/0
- Type: SSH, Port: 22, Source: YOUR_IP/32 (optional)

Outbound:
- Type: All traffic, Destination: 0.0.0.0/0
```

## Deployment Strategy Choice

### Option A: ECS Fargate (Recommended)
- [ ] ECS cluster created
- [ ] Task definition created
- [ ] Service created
- [ ] Load balancer configured
- [ ] Auto-scaling policies set

### Option B: EC2 with GPU
- [ ] EC2 instance launched (g4dn.xlarge or larger)
- [ ] GPU drivers installed
- [ ] Docker installed and configured
- [ ] Elastic IP assigned (or Route 53 CNAME)
- [ ] Security group attached

### Option C: Lambda + API Gateway
- [ ] ⚠️ **Not recommended** - cold start issues
- [ ] Only use for simple endpoints without TTS

## Deployment Execution

### ECS Deployment
```bash
# 1. Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/chatterbox-tts

# 2. Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 3. Create ECS cluster
aws ecs create-cluster --cluster-name chatterbox-cluster

# 4. Create service
aws ecs create-service \
  --cluster chatterbox-cluster \
  --service-name chatterbox-tts-service \
  --task-definition chatterbox-tts:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"

# 5. Verify deployment
aws ecs describe-services \
  --cluster chatterbox-cluster \
  --services chatterbox-tts-service
```

### EC2 Deployment
```bash
# 1. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 2. Clone repository
git clone https://github.com/your/repo.git
cd chatterbox

# 3. Configure environment
cp .env.example .env
nano .env

# 4. Start with Docker Compose
docker-compose up -d

# 5. Verify
curl http://localhost:5000/health
```

## Post-Deployment Validation

### Health Checks
- [ ] API responds to `/health` endpoint
- [ ] GPU detected and available
- [ ] Model loaded successfully
- [ ] CloudWatch logs streaming

### Functional Tests
```bash
# Health check
curl https://api.yourdomain.com/health

# Character list
curl https://api.yourdomain.com/characters

# Generate audio
curl -X POST https://api.yourdomain.com/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message", "character": "narrator"}'
```

### CORS Verification
- [ ] Test CORS headers from Vercel domain:
```bash
curl -H "Origin: https://yourdomain.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     https://api.yourdomain.com/generate-audio
```

### Performance Tests
- [ ] Generate audio with various text lengths
- [ ] Check response times (should be < 5 seconds)
- [ ] Monitor GPU memory usage
- [ ] Verify caching works (repeated requests are faster)

### Load Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Load test with 100 requests, 10 concurrent
ab -n 100 -c 10 https://api.yourdomain.com/health
```

## Frontend Integration

### Vercel Deployment
- [ ] Environment variable added:
  ```
  NEXT_PUBLIC_TTS_API_URL=https://api.yourdomain.com
  ```
- [ ] Frontend code updated with TTS client
- [ ] CORS domain in API's `CORS_ORIGINS`
- [ ] Frontend tested against production API

### Integration Testing
```typescript
// Test in Vercel frontend
const client = new ChatterboxTTSClient(
  process.env.NEXT_PUBLIC_TTS_API_URL
);
const result = await client.generateAudio({
  text: "Test from frontend",
  character: "narrator"
});
console.assert(result.success, "Integration failed");
```

## Monitoring Setup

### CloudWatch Monitoring
- [ ] Log group created: `/ecs/chatterbox-tts`
- [ ] CloudWatch alarms configured:
  - [ ] High CPU usage (> 80%)
  - [ ] High memory usage (> 90%)
  - [ ] API errors (4xx/5xx)
  - [ ] GPU memory critical
  - [ ] Health check failures

### Alarms Configuration
```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name chatterbox-high-cpu \
  --alarm-description "Alert when CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:region:account:topic
```

### Log Insights Queries
```
# Find errors in last hour
fields @timestamp, @message | filter @message like /ERROR/

# Monitor API latency
fields @duration | stats avg(@duration) by character

# GPU memory warnings
fields @timestamp, gpu_memory | filter gpu_memory > 14
```

## Auto-Scaling Configuration

### ECS Auto-Scaling
```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/chatterbox-cluster/chatterbox-tts-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 3

# Target tracking scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/chatterbox-cluster/chatterbox-tts-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration TargetValue=70,PredefinedMetricSpecification='{PredefinedMetricType=ECSServiceAverageCPUUtilization}'
```

## Backup & Recovery

- [ ] Model cache backed up to S3:
  ```bash
  aws s3 sync /app/.cache/torch s3://backup-bucket/chatterbox-cache/
  ```
- [ ] Snapshots scheduled for EBS volumes
- [ ] Disaster recovery plan documented

## Security Configuration

### Secrets Management
- [ ] AWS Secrets Manager setup (if needed)
- [ ] API keys rotated
- [ ] IAM policies principle of least privilege
- [ ] Security groups restrictive

### SSL/TLS
- [ ] ACM certificate created for domain
- [ ] ALB configured with HTTPS listener
- [ ] Redirect HTTP to HTTPS
- [ ] HSTS header enabled

### DDoS Protection
- [ ] AWS Shield Standard (automatic)
- [ ] AWS WAF rules configured (optional)
- [ ] Rate limiting implemented

## Documentation Updates

- [ ] Deployment guide updated with actual URLs
- [ ] API documentation published
- [ ] Frontend integration guide shared with team
- [ ] Runbook created for common issues
- [ ] Monitoring dashboard link documented

## Final Verification Checklist

Before going to production:

- [ ] All endpoints responding correctly
- [ ] Audio quality acceptable
- [ ] Response times acceptable (< 5s)
- [ ] No error spikes in CloudWatch
- [ ] Frontend successfully generating audio
- [ ] Caching working correctly
- [ ] GPU not running out of memory
- [ ] Logs are clean (no warnings/errors)
- [ ] Load tests passed
- [ ] Backup procedures verified
- [ ] Team trained on monitoring/troubleshooting
- [ ] Rollback plan prepared

## Rollback Plan

If issues occur:

1. **Immediate**: Scale down to 1 instance (stop new deployments)
2. **Investigation**: Check CloudWatch logs for errors
3. **Rollback**: Revert to previous task definition version
4. **Verification**: Run health checks and load tests
5. **Communication**: Update status with team/users

```bash
# Rollback ECS service
aws ecs update-service \
  --cluster chatterbox-cluster \
  --service chatterbox-tts-service \
  --task-definition chatterbox-tts:1  # Previous version

# Rollback EC2 deployment
docker-compose down
git checkout previous-tag
docker-compose up -d
```

## Post-Deployment Support

### First 24 Hours
- [ ] Monitor error rates continuously
- [ ] Check GPU memory trends
- [ ] Verify frontend integration working
- [ ] Respond to any critical issues

### First Week
- [ ] Analyze performance data
- [ ] Optimize resource allocation
- [ ] Fine-tune auto-scaling policies
- [ ] Document any issues encountered

### Ongoing
- [ ] Weekly health checks
- [ ] Monthly performance review
- [ ] Quarterly security audit
- [ ] Regular backup verification

---

## Quick Reference URLs

Once deployed:

- **Health Check**: `https://api.yourdomain.com/health`
- **Characters**: `https://api.yourdomain.com/characters`
- **Generate Audio**: `https://api.yourdomain.com/generate-audio` (POST)
- **AWS Console**: `https://console.aws.amazon.com/`
- **CloudWatch Logs**: `https://console.aws.amazon.com/logs/`
- **Frontend**: `https://yourdomain.vercel.app`

---

## Emergency Contacts

- [ ] AWS Support contact
- [ ] Team lead contact
- [ ] On-call engineer contact

---

**Status**: ⬜ Not Started | 🟡 In Progress | 🟢 Complete

Last Updated: [DATE]
Deployed By: [NAME]
Deployment Notes: [NOTES]
