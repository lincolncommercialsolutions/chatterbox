# Chatterbox TTS Scaling Guide

## Current Status
- **Server**: c6i.4xlarge (16 vCPU, 32GB RAM) at 35.174.4.196:5000
- **Performance**: 1.0-1.2s per request (very fast!)
- **Limitation**: Model is NOT thread-safe - requests MUST queue sequentially
- **Current behavior**: Multiple requests queue and process one at a time

## ⚠️ Why Concurrent Processing Won't Work
The Chatterbox TTS model maintains internal state that gets corrupted with concurrent access:
- Tested 3 concurrent requests: 2 failed with internal errors
- MODEL_LOCK is REQUIRED to prevent crashes
- This is a limitation of the underlying model, not the server

---

## 🚀 Recommended Scaling Strategies

### Option 1: Frontend Rate Limiting (EASIEST - Implement First)
**Best for**: 5-20 requests per minute
**Cost**: $0 (no backend changes)

```javascript
// In your Vercel API route /api/voice/tts.js
const lastRequestTime = global.lastTTSRequest || 0;
const timeSinceLastRequest = Date.now() - lastRequestTime;
const MIN_REQUEST_INTERVAL = 2000; // 2 seconds between requests

if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
  await new Promise(resolve => 
    setTimeout(resolve, MIN_REQUEST_INTERVAL - timeSinceLastRequest)
  );
}
global.lastTTSRequest = Date.now();

// Make your TTS request here
```

**Benefits**:
- Prevents server overload
- No backend changes needed
- Works with current setup
- Smooth user experience

---

### Option 2: Multiple TTS Server Instances + Load Balancer
**Best for**: 50+ requests per minute
**Cost**: ~$200-400/month (2-4 additional EC2 instances)

#### Architecture:
```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │  (AWS ALB/NLB)  │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
         ┌──────▼──────┐ ┌──▼──────┐ ┌──▼──────┐
         │ TTS Server  │ │ TTS     │ │ TTS     │
         │ Instance 1  │ │ Instance│ │ Instance│
         │ :5000       │ │ 2 :5000 │ │ 3 :5000 │
         └─────────────┘ └─────────┘ └─────────┘
```

#### Implementation Steps:

**Step 1: Create AMI from Current Instance**
```bash
# From your local machine
aws ec2 create-image \
  --instance-id i-01cc4c92d83a1b6da \
  --name "chatterbox-tts-v1" \
  --description "Chatterbox TTS with 4 custom voices" \
  --region us-east-1
```

**Step 2: Launch Additional Instances**
```bash
# Launch 2 more instances from the AMI
aws ec2 run-instances \
  --image-id ami-xxxxx \
  --instance-type c6i.4xlarge \
  --count 2 \
  --region us-east-1 \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx
```

**Step 3: Create Application Load Balancer**
```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name chatterbox-tts-lb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application \
  --region us-east-1

# Create Target Group
aws elbv2 create-target-group \
  --name chatterbox-tts-targets \
  --protocol HTTP \
  --port 5000 \
  --vpc-id vpc-xxxxx \
  --health-check-path /health \
  --health-check-interval-seconds 30

# Register instances
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-01cc4c92d83a1b6da Id=i-xxxxx Id=i-yyyyy
```

**Step 4: Update Frontend**
```javascript
// Change your API endpoint from:
const TTS_API = 'http://35.174.4.196:5000'

// To:
const TTS_API = 'http://chatterbox-tts-lb-123456.us-east-1.elb.amazonaws.com'
```

**Expected Performance**:
- 3 instances × 1 req/sec = 3 concurrent requests
- 180 requests per minute capacity
- Each instance costs ~$150/month

---

### Option 3: Request Caching (BEST ROI)
**Best for**: Repeated phrases/common use cases
**Cost**: $0-20/month (Redis/DynamoDB)

Many TTS use cases have repeated phrases. Cache generated audio:

```javascript
// Vercel API route with caching
import { createClient } from 'redis';

const redis = createClient({ url: process.env.REDIS_URL });

export default async function handler(req, res) {
  const { text, character } = req.body;
  const cacheKey = `tts:${character}:${text}`;
  
  // Check cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return res.json(JSON.parse(cached));
  }
  
  // Generate and cache
  const result = await fetch('http://35.174.4.196:5000/tts-json', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, character })
  });
  const data = await result.json();
  
  // Cache for 7 days
  await redis.setEx(cacheKey, 604800, JSON.stringify(data));
  
  return res.json(data);
}
```

**Benefits**:
- Instant response for cached phrases
- Reduces load by 50-80% for typical use
- Upstash Redis free tier: 10,000 requests/day

---

### Option 4: Queue System with Status Feedback
**Best for**: Batch processing, async workflows
**Cost**: ~$5-20/month (AWS SQS + Lambda)

```javascript
// Submit to queue instead of waiting
const queueResponse = await fetch('/api/voice/queue', {
  method: 'POST',
  body: JSON.stringify({ text, character, userId })
});
const { requestId } = await queueResponse.json();

// Poll for completion
const checkStatus = async () => {
  const status = await fetch(`/api/voice/status/${requestId}`);
  const { ready, audioUrl } = await status.json();
  if (ready) {
    // Use audioUrl
  } else {
    // Show progress, retry in 2s
  }
};
```

---

## 💰 Cost-Benefit Analysis

| Solution | Monthly Cost | Capacity Increase | Implementation Time |
|----------|-------------|-------------------|-------------------|
| Frontend Rate Limiting | $0 | 1x (better UX) | 10 minutes |
| Caching (Redis) | $0-20 | 2-5x (for repeats) | 2 hours |
| 2 More Instances + ALB | $300-350 | 3x | 4-6 hours |
| Queue System | $5-20 | ∞ (async) | 1 day |

---

## 🎯 Recommended Implementation Order

### Phase 1 (Do Now - 30 minutes):
1. **Add frontend rate limiting** - prevents overload
2. **Monitor current usage** - understand actual load

### Phase 2 (If needed - 2-4 hours):
3. **Implement caching** - huge ROI for common phrases
4. **Add request queuing** - better UX for multiple requests

### Phase 3 (If scaling needed - 1 day):
5. **Launch 1-2 more instances** - test load balancing
6. **Set up ALB** - distribute traffic
7. **Monitor and optimize** - adjust instance count

---

## 📊 Current Performance Metrics

**Single Instance (c6i.4xlarge)**:
- Generation time: 1.0-1.2s per request
- Maximum throughput: ~60 requests/minute (with queuing)
- Cost: ~$150/month

**With 3 Instances + ALB**:
- Generation time: 1.0-1.2s per request (unchanged)
- Maximum throughput: ~180 requests/minute
- Cost: ~$500/month

---

## 🔧 Monitoring & Optimization

### Key Metrics to Track:
```python
# Add to api_server.py
import time
import threading

request_queue_size = 0
request_wait_times = []

@app.route('/metrics')
def metrics():
    return {
        'queue_size': request_queue_size,
        'avg_wait_time': sum(request_wait_times[-100:]) / len(request_wait_times[-100:]),
        'requests_per_minute': len([t for t in request_wait_times if time.time() - t < 60])
    }
```

### Health Check Endpoint (already exists):
```bash
curl http://35.174.4.196:5000/health
# Response: {"status": "healthy", "timestamp": "..."}
```

---

## 🚨 What WON'T Work

❌ **Removing MODEL_LOCK** - Causes crashes and corrupted audio
❌ **Threading on single instance** - Model isn't thread-safe
❌ **Just adding more CPU/RAM** - Doesn't enable concurrency
❌ **Async processing on same model** - Still hits thread-safety issues

---

## 📝 Quick Start: Frontend Rate Limiting

The fastest win - add this to your Vercel deployment NOW:

```typescript
// lib/ttsThrottle.ts
let lastRequestTime = 0;
const MIN_INTERVAL = 2000; // 2 seconds

export async function throttledTTSRequest(text: string, character: string) {
  const now = Date.now();
  const timeSinceLastRequest = now - lastRequestTime;
  
  if (timeSinceLastRequest < MIN_INTERVAL) {
    await new Promise(resolve => 
      setTimeout(resolve, MIN_INTERVAL - timeSinceLastRequest)
    );
  }
  
  lastRequestTime = Date.now();
  
  const response = await fetch('http://35.174.4.196:5000/tts-json', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, character })
  });
  
  return response.json();
}
```

Use this instead of direct fetch calls to your TTS endpoint!

---

## Need Help?
- Current server: `35.174.4.196:5000`
- Instance: `i-01cc4c92d83a1b6da` (c6i.4xlarge)
- Region: `us-east-1`
- Working voices: andrew_tate, peter_griffin, lois_griffin, trump
