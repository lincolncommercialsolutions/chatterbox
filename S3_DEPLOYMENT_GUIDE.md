# Chatterbox TTS with S3 Deployment Guide

Complete guide for deploying Chatterbox TTS on S3 with OpenRouter AI integration for your Vercel frontend.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Frontend Integration](#frontend-integration)
6. [S3 Management](#s3-management)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- AWS Account with S3 access
- AWS credentials (Access Key ID & Secret Access Key)
- GPU-enabled machine (recommended for faster inference)

### 2. Install Dependencies

```bash
cd /home/linkl0n/chatterbox
pip install -r requirements.txt
pip install Flask flask-cors boto3 python-dotenv
```

### 3. Configure Environment

Edit `.env` file:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1

# S3 Configuration
S3_ENABLED=true
S3_BUCKET_NAME=your-bucket-name
S3_AUDIO_PREFIX=chatterbox/audio/
S3_VOICES_PREFIX=chatterbox/voices/
S3_PRESIGNED_URL_EXPIRY=3600

# API Configuration
API_PORT=5000
CORS_ORIGINS=https://yourdomain.vercel.app,https://yourdomain-staging.vercel.app

# Character Configuration
DEFAULT_CHARACTER=assistant
CHARACTER_CONFIG_FILE=character_voices.json
```

### 4. Create S3 Bucket

```bash
python s3_manager.py create-bucket
```

Or use AWS CLI:

```bash
aws s3 mb s3://your-bucket-name --region us-east-1
```

### 5. Start API Server

```bash
python chatterbox/api_server.py
```

Or with Gunicorn for production:

```bash
gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 chatterbox.api_server:app
```

---

## Architecture

### Component Flow

```
┌─────────────────────┐
│  Vercel Frontend    │
│  (Next.js/React)    │
└──────────┬──────────┘
           │
           │ 1. User sends message
           │
┌──────────▼──────────────────────┐
│  OpenRouter API                  │
│  (AI Response Generation)        │
└──────────┬──────────────────────┘
           │
           │ 2. AI generates response text
           │
┌──────────▼──────────────────────┐
│  Chatterbox TTS API              │
│  /generate-audio endpoint        │
└──────────┬──────────────────────┘
           │
           │ 3. Process request:
           │    - Load character config
           │    - Load voice profile
           │    - Generate speech
           │
┌──────────▼──────────────────────┐
│  Audio Generation (GPU/CPU)      │
│  MTL TTS Model                   │
└──────────┬──────────────────────┘
           │
           │ 4. Generated audio WAV
           │
┌──────────▼──────────────────────┐
│  S3 Upload                       │
│  Store audio file                │
└──────────┬──────────────────────┘
           │
           │ 5. Return S3 URL or base64
           │
┌──────────▼──────────────────────┐
│  Frontend Audio Player           │
│ Play audio to user               │
└──────────────────────────────────┘
```

### File Structure

```
chatterbox/
├── api_server.py                 # Main Flask API server
├── s3_manager.py                 # S3 bucket management utilities
├── character_voices.json         # Character & voice configurations
├── integration_test.py           # End-to-end tests
├── .env                          # Environment configuration
├── requirements.txt              # Python dependencies
└── src/
    └── chatterbox/
        ├── mtl_tts.py           # TTS model interface
        └── ...
```

---

## Configuration

### Environment Variables

#### AWS/S3 Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key | Required |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | Required |
| `AWS_REGION` | AWS Region | `us-east-1` |
| `S3_ENABLED` | Enable S3 storage | `true` |
| `S3_BUCKET_NAME` | S3 bucket name | Required if S3_ENABLED |
| `S3_AUDIO_PREFIX` | Prefix for audio files | `chatterbox/audio/` |
| `S3_PRESIGNED_URL_EXPIRY` | URL expiry in seconds | `3600` |

#### API Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PORT` | Server port | `5000` |
| `API_HOST` | Server host | `0.0.0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `MAX_TEXT_LENGTH` | Max text length | `500` |
| `DEFAULT_MAX_TOKENS` | Default generation tokens | `400` |
| `CACHE_ENABLED` | Enable response cache | `true` |
| `CACHE_SIZE` | Cache size | `100` |

#### Character Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_CHARACTER` | Default character | `assistant` |
| `CHARACTER_CONFIG_FILE` | Config file path | `character_voices.json` |

### Character Configuration (character_voices.json)

```json
{
  "voices": {
    "narrator": {
      "name": "Professional Narrator",
      "language": "en",
      "audio_url": "https://...",
      "parameters": {
        "exaggeration": 0.4,
        "temperature": 0.6,
        "cfg_weight": 0.7
      }
    }
  },
  "characters": {
    "assistant": {
      "name": "AI Assistant",
      "voice_id": "friendly",
      "description": "Friendly helper",
      "system_prompt": "Be helpful and friendly"
    }
  }
}
```

---

## Deployment

### Local Development

```bash
# 1. Configure .env
# 2. Create S3 bucket
python s3_manager.py create-bucket

# 3. Start API server
python chatterbox/api_server.py

# 4. In another terminal, run tests
python integration_test.py
```

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install CUDA runtime (if using GPU)
# RUN apt-get update && apt-get install -y cuda-toolkit

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install Flask flask-cors boto3 python-dotenv

COPY . .

ENV PYTHONUNBUFFERED=1
ENV API_PORT=5000

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "chatterbox.api_server:app"]
```

Build and run:

```bash
docker build -t chatterbox-tts .
docker run --gpus all -p 5000:5000 --env-file .env chatterbox-tts
```

### AWS EC2 Deployment

```bash
# 1. Launch g4dn.xlarge or g4dn.2xlarge instance
# 2. Install Python 3.10+
# 3. Clone repository
git clone <repo-url>
cd chatterbox

# 4. Install dependencies
pip install -r requirements.txt
pip install Flask flask-cors boto3 python-dotenv

# 5. Configure .env with AWS credentials
cp .env.example .env
# Edit .env with your credentials

# 6. Create S3 bucket
python s3_manager.py create-bucket

# 7. Start with systemd or supervisor
# Create /etc/systemd/system/chatterbox.service
```

---

## Frontend Integration

### React/Next.js Setup

```typescript
import { createTTSClient } from '@/lib/chatterbox-tts-client';

const ttsClient = createTTSClient(
  process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000'
);

// Generate audio for OpenRouter response
async function handleAIResponse(text: string, character: string = 'assistant') {
  try {
    const result = await ttsClient.generateAudio({
      text,
      character,
      returnFormat: 'url',  // Returns S3 URL instead of base64
    });

    // Play audio
    const audio = new Audio(result.audio_url);
    audio.play();
  } catch (error) {
    console.error('TTS generation failed:', error);
  }
}
```

### OpenRouter Integration

```typescript
// 1. Get AI response from OpenRouter
const aiResponse = await getOpenRouterResponse(userMessage);

// 2. Generate audio with Chatterbox
const audioResult = await ttsClient.generateAudio({
  text: aiResponse.message.content,
  character: selectedCharacter,
  returnFormat: 'url',
  presigned: false,  // Use public S3 URL
});

// 3. Combine response and audio
displayMessage({
  text: aiResponse.message.content,
  audioUrl: audioResult.audio_url,
  character: selectedCharacter,
  duration: audioResult.duration,
});
```

---

## S3 Management

### List Files

```bash
python s3_manager.py list
```

### Upload Audio

```bash
python s3_manager.py upload /path/to/audio.wav
```

### Verify Connection

```bash
python test_s3_connection.py
```

### AWS CLI Commands

```bash
# List bucket contents
aws s3 ls s3://your-bucket-name/chatterbox/audio/ --recursive

# Download file
aws s3 cp s3://your-bucket-name/chatterbox/audio/file.wav ./

# Delete old files
aws s3 rm s3://your-bucket-name/chatterbox/audio/ --recursive --exclude "*" --include "*.wav"

# Set lifecycle policy (delete old files automatically)
aws s3api put-bucket-lifecycle-configuration \
  --bucket your-bucket-name \
  --lifecycle-configuration file://lifecycle.json
```

Lifecycle policy (lifecycle.json):

```json
{
  "Rules": [
    {
      "Id": "DeleteOldAudio",
      "Status": "Enabled",
      "Prefix": "chatterbox/audio/",
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

---

## Testing

### Health Check

```bash
curl http://localhost:5000/health
```

### Generate Audio (base64)

```bash
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "character": "assistant",
    "return_format": "base64"
  }'
```

### Generate Audio (S3 URL)

```bash
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "character": "assistant",
    "return_format": "url"
  }'
```

### Get Available Characters

```bash
curl http://localhost:5000/characters
```

### Get Available Voices

```bash
curl http://localhost:5000/voices
```

### Run Integration Tests

```bash
python integration_test.py
```

---

## Troubleshooting

### S3 Connection Issues

**Error: "The requested bucket name is not available"**

- Bucket names are globally unique in AWS
- Choose a different bucket name with your account ID or date

**Error: "Access Denied (403)"**

- Check AWS credentials in .env
- Verify IAM permissions include S3 access
- Check bucket policy if using cross-account access

**Error: "NoCredentialsError"**

- AWS credentials not found or not set
- Check `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in .env
- Alternatively, use AWS CLI credentials: `aws configure`

### Audio Generation Issues

**Error: "Failed to load model"**

- First request may take longer as model loads
- Ensure sufficient GPU/CPU memory
- Check DEVICE setting (cuda vs cpu)

**Error: "Out of memory"**

- Reduce `BATCH_SIZE` in .env
- Use CPU instead of GPU
- Increase system memory

**Error: "Text too long"**

- Current limit is 500 characters
- Modify `MAX_TEXT_LENGTH` in .env

### CORS Issues

**Error: "No 'Access-Control-Allow-Origin' header"**

- Update `CORS_ORIGINS` in .env to include your domain
- Ensure frontend URL matches exactly

### Performance Issues

**API is slow**

- Enable GPU acceleration if available
- Check GPU memory usage
- Adjust `BATCH_SIZE` setting
- Use caching (`CACHE_ENABLED=true`)

**S3 uploads are slow**

- Check AWS region - use region closest to your server
- Enable multipart upload for large files (handled automatically)
- Consider using CloudFront CDN for faster downloads

---

## Best Practices

1. **Security**
   - Never commit AWS credentials to version control
   - Use IAM roles for EC2 instances instead of access keys
   - Restrict bucket access with bucket policies
   - Enable S3 encryption

2. **Performance**
   - Enable response caching for repeated texts
   - Use presigned URLs for privacy-sensitive content
   - Implement CloudFront CDN for global distribution
   - Monitor GPU memory usage

3. **Cost Optimization**
   - Set S3 lifecycle policies to delete old audio files
   - Use Spot instances for non-critical deployments
   - Monitor S3 transfer costs
   - Consider using S3 Intelligent-Tiering

4. **Monitoring**
   - Enable CloudWatch logging
   - Set up alerts for failed requests
   - Monitor S3 bucket size and costs
   - Track API latency and error rates

---

## API Reference

### POST /generate-audio

Main endpoint for OpenRouter integration.

**Request:**
```json
{
  "text": "Response text from OpenRouter",
  "character": "assistant",
  "voice_id": "friendly",
  "return_format": "url",
  "presigned": false,
  "max_tokens": 400
}
```

**Response:**
```json
{
  "success": true,
  "audio_url": "https://bucket.s3.region.amazonaws.com/...",
  "sample_rate": 24000,
  "duration": 2.5,
  "character": "assistant",
  "voice_id": "friendly",
  "storage": "s3",
  "generation_time_ms": 1234
}
```

### GET /characters

List available characters.

### GET /characters/{characterId}

Get character details.

### POST /characters/{characterId}/voice

Change character's voice.

### GET /voices

List available voices.

### GET /health

Health check with GPU info.

---

## Support & Contribution

For issues, feature requests, or contributions, please refer to the main repository documentation.
