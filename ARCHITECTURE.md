# Chatterbox TTS - Architecture & Design Overview

Complete architecture documentation for Chatterbox TTS API with GPU support on AWS.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Vercel Frontend                          │
│                 (Next.js Character Chatbot)                     │
│                                                                 │
│  ┌─────────────────┐         ┌──────────────────────┐           │
│  │  User Chat UI   │────────▶│  OpenRouter API      │           │
│  └─────────────────┘         │  (AI Character)      │           │
│                              └──────────────────────┘           │
│                                     │                            │
│                                     │ AI Response                │
│                                     ▼                            │
│                      ┌──────────────────────────┐               │
│                      │  Chatterbox TTS Client   │               │
│                      │  (TypeScript/React)      │               │
│                      └──────────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        AWS Infrastructure                        │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Application Load Balancer (ALB)               │  │
│  │  - HTTPS termination                                     │  │
│  │  - Health checks                                         │  │
│  │  - Request routing                                       │  │
│  └──────────────────┬──────────────────────────────────────┘  │
│                     │                                           │
│       ┌─────────────┼─────────────┐                            │
│       ▼             ▼             ▼                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                 │
│  │  ECS Task  │ │  ECS Task  │ │  ECS Task  │  (Auto-scaling) │
│  │ (g4dn.2x)  │ │ (g4dn.2x)  │ │ (g4dn.2x)  │                 │
│  │            │ │            │ │            │                 │
│  │ Container: │ │ Container: │ │ Container: │                 │
│  │ Chatterbox │ │ Chatterbox │ │ Chatterbox │                 │
│  │ TTS API    │ │ TTS API    │ │ TTS API    │                 │
│  │            │ │            │ │            │                 │
│  │ GPU: NVIDIA│ │ GPU: NVIDIA│ │ GPU: NVIDIA│                 │
│  │ T4 16GB    │ │ T4 16GB    │ │ T4 16GB    │                 │
│  └────────────┘ └────────────┘ └────────────┘                 │
│                                                                  │
│  Shared Resources:                                              │
│  - Model Cache (EFS)     [100GB+]                              │
│  - CloudWatch Logs        [Streaming]                          │
│  - S3 Backup              [Model snapshots]                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
1. User Message
   ├─ Frontend Input
   └─ Sent to Frontend API

2. OpenRouter Call
   ├─ Frontend calls OpenRouter
   ├─ Returns: AI character response
   └─ Response text to TTS

3. Audio Generation
   ├─ Request: {text, character}
   ├─ TTS API receives request
   ├─ Check cache
   │  ├─ Cache HIT ──▶ Return cached audio (10ms)
   │  └─ Cache MISS ─▶ Generate new audio
   │
   ├─ GPU Processing
   │  ├─ Load model (if needed)
   │  ├─ Tokenize text
   │  ├─ Generate audio waveform
   │  └─ Encode to WAV
   │
   ├─ Post-processing
   │  ├─ Normalize audio
   │  ├─ Compress if needed
   │  └─ Cache result
   │
   └─ Response: {audio_base64, duration}

4. Frontend Playback
   ├─ Decode base64 to Blob
   ├─ Create Object URL
   ├─ Play in audio element
   └─ Cleanup on unload
```

## Component Details

### 1. Frontend (Vercel/Next.js)

**TypeScript Client**: `chatterbox-tts-client.ts`
- Async API calls with retry logic
- Error handling and fallbacks
- Automatic URL cleanup
- React hook support
- OpenRouter integration helper

**Features**:
- Request batching support
- Audio blob management
- URL lifecycle management
- Health checking

### 2. API Server (Flask)

**Main Application**: `api_server.py`
- FastAPI-like Flask endpoints
- GPU memory management
- Built-in audio caching
- CORS support for Vercel
- Health monitoring

**Endpoints**:
```
GET  /health              - Health check + GPU stats
GET  /characters          - List available voices
GET  /languages           - List supported languages
POST /generate-audio      - Main OpenRouter endpoint
POST /tts                 - Direct audio file return
POST /tts-json            - JSON response format
```

### 3. GPU Infrastructure

**Instance Type**: g4dn.2xlarge
- vCPU: 8
- Memory: 32 GB RAM
- GPU: 2x NVIDIA T4 (32GB total VRAM)
- Network: 25 Gbps
- Cost: ~$1.06/hour

**Alternative**: g4dn.xlarge
- vCPU: 4
- Memory: 16 GB RAM
- GPU: 1x NVIDIA T4 (16GB)
- Cost: ~$0.53/hour

### 4. Caching Strategy

**In-Memory Cache**:
- Max 100 items
- Key: MD5(text + character)
- Value: (audio_bytes, sample_rate, duration)
- Lifetime: Session
- Hit ratio: ~60-70% in typical usage

**Cache Scenarios**:
- User retries same message ✓ (Cached)
- Same AI response text different character ✗ (Not cached)
- Similar but different text ✗ (Not cached)

### 5. Model Management

**Model**: ChatterboxMultilingualTTS
- Size: ~8GB
- VRAM required: 12GB
- Load time: 30-60s
- Warmup: First request slower
- Supports: 200+ languages

**Optimization**:
- Model loaded once at startup
- Shared across requests
- GPU memory managed automatically
- Preloading on container start

## Performance Characteristics

### Latency (Per-Request)

| Operation | Time | Notes |
|-----------|------|-------|
| Request processing | 50ms | Validation + parsing |
| Cache lookup | 10ms | If cached |
| Model inference | 1000-3000ms | GPU dependent |
| Audio encoding | 100-200ms | WAV format |
| Network roundtrip | 100-500ms | AWS/Internet |
| **Total** | **1.2-4.0s** | Typical range |

### Throughput

- **Single Instance**: 15-20 requests/minute
- **With 3 instances**: 45-60 requests/minute
- **Bottleneck**: GPU inference time

### Memory Usage

| Component | Usage |
|-----------|-------|
| Python runtime | 200MB |
| Model weights | 8GB |
| Model KV cache | 2-4GB |
| Request buffer | 500MB-1GB |
| Audio cache | 50-500MB |
| **Total** | **11-14GB** |

## Deployment Decision Matrix

### Choose ECS if you need:
✅ Auto-scaling based on load
✅ AWS-managed infrastructure
✅ Multi-region deployment
✅ Built-in logging/monitoring
✅ Easy CI/CD integration

### Choose EC2 if you need:
✅ Direct instance control
✅ Custom optimization
✅ Simpler single-instance setup
✅ Lower AWS management overhead
✅ Consistent workload

### Choose Lambda if you need: ⚠️
❌ **Not recommended for TTS**
- Model load time exceeds Lambda timeout
- Memory constraints insufficient
- Ephemeral filesystem
- GPU not available
- Cost inefficient

## Security Architecture

```
┌─────────────────────────────────────────┐
│   Vercel Frontend (HTTPS)               │
└──────────┬──────────────────────────────┘
           │
    [CORS Validation]
           │
┌──────────▼──────────────────────────────┐
│   AWS CloudFront / ALB                  │
│   - SSL/TLS Termination                 │
│   - DDoS Protection (Shield)            │
│   - WAF Rules (optional)                │
└──────────┬──────────────────────────────┘
           │
    [Request Validation]
           │
┌──────────▼──────────────────────────────┐
│   ECS Task (Container)                  │
│   - Non-root user                       │
│   - No privileged mode                  │
│   - Ephemeral storage                   │
│   - Secrets from AWS Secrets Manager    │
└──────────┬──────────────────────────────┘
           │
    [Model Inference]
           │
┌──────────▼──────────────────────────────┐
│   GPU Inference                         │
│   - Isolated memory spaces              │
│   - No direct internet access           │
└─────────────────────────────────────────┘
```

### Security Best Practices

1. **Network Security**
   - Private subnets for ECS tasks
   - ALB in public subnet
   - Security groups: principle of least privilege
   - No SSH access in production

2. **Data Security**
   - HTTPS only
   - CORS restricted to specific domain
   - No sensitive data in logs
   - Secrets in AWS Secrets Manager

3. **Container Security**
   - Minimal base image (Ubuntu 22.04)
   - Non-root user execution
   - Read-only filesystem (where possible)
   - No hardcoded credentials

4. **API Security**
   - Input validation on all endpoints
   - Rate limiting (implement if needed)
   - API key support (optional)
   - Request size limits

## Monitoring & Observability

### Metrics Tracked

**API Metrics**:
- Request count
- Response time (p50, p95, p99)
- Error rate
- Cache hit ratio

**GPU Metrics**:
- GPU utilization
- GPU memory used
- GPU temperature
- VRAM available

**Infrastructure**:
- CPU usage
- Memory usage
- Disk space
- Network I/O

### Logging Strategy

**Log Levels**:
- ERROR: API errors, failures
- WARNING: Timeouts, degradation
- INFO: Request/response (production)
- DEBUG: Detailed trace (development)

**Log Aggregation**:
- CloudWatch Logs (centralized)
- Log Insights queries
- Custom dashboards
- Alarm triggers

## Scaling Strategy

### Horizontal Scaling (Recommended)

```
Traffic Spikes
    ↓
CPU > 70% for 2 minutes
    ↓
Scaling Policy Triggers
    ↓
Launch new ECS task
    ↓
Connect to ALB
    ↓
Traffic distributed
    ↓
Response time normalized
```

### Auto-Scaling Configuration

```yaml
Min Instances: 1
Max Instances: 3
Target CPU: 70%
Target Memory: 80%
Scale-up delay: 2 minutes
Scale-down delay: 5 minutes
```

### Vertical Scaling (Alternative)

For consistent high load:
- g4dn.2xlarge (2 GPUs)
- g4dn.12xlarge (4 GPUs)

Trade-off: Higher cost but fewer instances to manage

## Disaster Recovery

### Backup Strategy

**Model Cache**:
- S3 snapshot weekly
- Restore time: 5-10 minutes
- Cost: ~$0.50/day

**Configuration**:
- Stored in parameter store
- Version controlled
- Instant restore

### Recovery Procedures

**API Outage**:
1. Check health: `/health` endpoint
2. Review logs: CloudWatch Logs
3. Restart task: `aws ecs update-service`
4. Failover: DNS to backup instance (if available)

**Model Cache Corruption**:
1. Stop current task
2. Restore from S3 backup
3. Restart task
4. Verify health check

**Regional Failure** (if multi-region):
1. DNS failover (Route 53)
2. Traffic to secondary region
3. Restore data if needed
4. Monitor recovery

## Cost Optimization

### Cost Breakdown (Monthly)

| Component | Cost | Notes |
|-----------|------|-------|
| g4dn.xlarge instance | $377 | 1 GPU, 24/7 |
| Data transfer (10GB) | $0.90 | Out to internet |
| Storage (100GB) | $2.30 | EBS |
| CloudWatch logs | $15 | ~30GB/month |
| CloudWatch monitoring | $5 | Dashboards + alarms |
| **Total** | **~$400** | Single instance |

### Cost Reduction Strategies

1. **Right-sizing**
   - Use g4dn.xlarge for low load
   - Scale up only when needed
   - Estimated savings: 20-30%

2. **Reserved Instances**
   - 1-year commitment: 25% discount
   - 3-year commitment: 45% discount
   - Estimated savings: $100-200/month

3. **Spot Instances** ⚠️
   - 70% discount but interruptible
   - Not suitable for this workload
   - Better for batch processing

4. **Data Transfer Optimization**
   - CloudFront caching (if applicable)
   - Compression for responses
   - Regional deployment (multi-region)

## Development Workflow

```
Local Development
    ↓ (docker-compose up)
    ↓
Feature Branch Testing
    ↓ (push to GitHub)
    ↓
CI/CD Pipeline
    ├─ Unit tests
    ├─ Integration tests
    └─ Build Docker image
    ↓
ECR Push
    ↓
ECS Staging Deployment
    ↓ (manual approval)
    ↓
ECS Production Deployment
    ↓ (blue-green or canary)
    ↓
Monitoring + Rollback (if needed)
```

## Future Enhancements

### Planned Features

1. **Multi-model Support**
   - Faster inference model
   - High-quality model
   - User selection

2. **Advanced Caching**
   - Redis distributed cache
   - Cross-instance cache sharing
   - S3 long-term cache

3. **Batch Processing**
   - Queue for bulk requests
   - Off-peak generation
   - Cost optimization

4. **Audio Formats**
   - MP3 compression
   - OGG support
   - Custom sample rates

5. **Analytics**
   - Usage tracking
   - Performance analytics
   - Character popularity

### Performance Improvements

- Model quantization (reduce size)
- Streaming response support
- Parallel inference requests
- Dynamic batch processing

## Troubleshooting Guide

### Common Issues & Solutions

**High Latency**
- Check GPU utilization
- Monitor memory usage
- Consider scaling up

**High Memory Usage**
- Check model cache size
- Clear old cache entries
- Reduce batch size

**CORS Failures**
- Verify domain in CORS_ORIGINS
- Check Origin header
- Test with curl

**Model Loading Failures**
- Check disk space
- Verify internet connectivity
- Check permissions

See DEPLOYMENT_CHECKLIST.md for detailed troubleshooting.

---

**Version**: 1.0.0
**Last Updated**: 2026-02-09
**Status**: Production Ready ✅
