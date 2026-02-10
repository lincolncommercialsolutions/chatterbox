# Chatterbox TTS with S3 - Complete Setup Guide

**Chatterbox TTS deployed on S3 with pre-selected character voices for OpenRouter AI integration on your Vercel frontend.**

This setup provides:
- ✓ GPU-accelerated TTS generation
- ✓ S3-backed audio storage with CDN
- ✓ Pre-configured character voices
- ✓ OpenRouter AI integration ready
- ✓ Presigned URL support for private audio
- ✓ Complete REST API for frontend integration

---

## 📋 Table of Contents

- [Quick Start (5 minutes)](#quick-start)
- [What's New](#whats-new)
- [Architecture Overview](#architecture-overview)
- [Complete Configuration](#configuration)
- [Character Voice System](#character-voice-system)
- [API Usage](#api-usage)
- [Deployment](#deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd /home/linkl0n/chatterbox

# Install required packages
pip install Flask flask-cors boto3 python-dotenv

# Or use the provided script
bash setup.sh
```

### Step 2: Configure AWS Credentials

Edit `.env`:

```env
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1

S3_ENABLED=true
S3_BUCKET_NAME=chatterbox-audio-231399652064
```

### Step 3: Validate Configuration

```bash
python validate_config.py
```

### Step 4: Create S3 Bucket

```bash
python s3_manager.py create-bucket
```

### Step 5: Start the API Server

```bash
python chatterbox/api_server.py
```

The server will start on `http://localhost:5000`

### Step 6: Test the Setup

In another terminal:

```bash
python integration_test.py
```

---

## ✨ What's New

### S3 Integration
- ✓ Audio files automatically uploaded to S3
- ✓ Public URLs for direct access
- ✓ Presigned URLs for temporary/private access
- ✓ Configurable expiration times
- ✓ Bucket lifecycle management support

### Character Voice System
- ✓ **6 Pre-configured characters**: narrator, assistant, luna, sage, echo, zephyr
- ✓ **6 Voice profiles**: narrator, friendly, expert, mysterious, calm, energetic
- ✓ **Customizable parameters**: exaggeration, temperature, cfg_weight
- ✓ **JSON-based configuration**: Easy to modify character_voices.json
- ✓ **Dynamic voice switching**: Change character voices at runtime

### OpenRouter Integration
- ✓ Dedicated `/generate-audio` endpoint for AI responses
- ✓ Character preset support
- ✓ Automatic voice selection based on character
- ✓ Caching for repeated audio generation
- ✓ Base64 or S3 URL response options

### Frontend Ready
- ✓ TypeScript client with full type safety
- ✓ React hooks for seamless integration
- ✓ Error handling and retries
- ✓ Audio playback utilities
- ✓ Batch processing support

---

## 🏗️ Architecture Overview

```
Vercel Frontend (Next.js/React)
           ↓
OpenRouter AI Response Generation
           ↓
Chatterbox TTS API (/generate-audio)
           ↓
Character Voice Selection
           ↓
GPU-Accelerated TTS Model
           ↓
Audio File Generated
           ↓
S3 Upload
           ↓
Return S3 URL (or base64)
           ↓
Frontend Audio Player
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `api_server.py` | Flask REST API server with all endpoints |
| `character_voices.json` | Configuration for voices, characters, and presets |
| `s3_manager.py` | S3 bucket management utilities |
| `integration_test.py` | Complete end-to-end tests |
| `validate_config.py` | Configuration validation tool |
| `frontend/chatterbox-tts-client.ts` | TypeScript client library |

---

## ⚙️ Configuration

### Environment Variables

Create or edit `.env`:

```env
# ============ AWS & S3 Configuration ============
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1

# S3 Audio Storage
S3_ENABLED=true
S3_BUCKET_NAME=chatterbox-audio-231399652064
S3_AUDIO_PREFIX=chatterbox/audio/
S3_VOICES_PREFIX=chatterbox/voices/
S3_PRESIGNED_URL_EXPIRY=3600

# ============ API Server Configuration ============
API_PORT=5000
API_HOST=0.0.0.0
LOG_LEVEL=INFO

# ============ CORS Configuration (for Vercel frontend) ============
CORS_ORIGINS=http://localhost:3000,https://yourdomain.vercel.app

# ============ TTS Generation Settings ============
MAX_TEXT_LENGTH=500
DEFAULT_MAX_TOKENS=400
BATCH_SIZE=1
CACHE_ENABLED=true
CACHE_SIZE=100

# ============ Character Voice Configuration ============
DEFAULT_CHARACTER=assistant
CHARACTER_CONFIG_FILE=character_voices.json
```

### Character Configuration (character_voices.json)

Define voices and characters:

```json
{
  "voices": {
    "narrator": {
      "name": "Professional Narrator",
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
      "description": "Friendly AI assistant"
    }
  }
}
```

---

## 🎭 Character Voice System

### Available Characters

| Character | Voice | Use Case |
|-----------|-------|----------|
| **narrator** | narrator | Storytelling, narration |
| **assistant** | friendly | General conversations |
| **luna** | mysterious | Engaging storytelling |
| **sage** | calm | Educational content |
| **echo** | expert | Technical discussions |
| **zephyr** | energetic | Motivational content |

### Using Characters in API

```bash
# Generate audio with specific character
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I am your AI assistant!",
    "character": "assistant",
    "return_format": "url"
  }'
```

### Changing Character Voices

```bash
# Switch assistant to use expert voice
curl -X POST http://localhost:5000/characters/assistant/voice \
  -H "Content-Type: application/json" \
  -d '{"voice_id": "expert"}'
```

---

## 🔌 API Usage

### Health Check

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "s3": {
    "enabled": true,
    "bucket": "chatterbox-audio-231399652064",
    "region": "us-east-1"
  }
}
```

### Generate Audio for OpenRouter Response

**Primary endpoint for frontend integration:**

```bash
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The AI character response from OpenRouter",
    "character": "assistant",
    "return_format": "url",
    "presigned": false
  }'
```

Response:
```json
{
  "success": true,
  "audio_url": "https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/...",
  "sample_rate": 24000,
  "duration": 2.5,
  "character": "assistant",
  "voice_id": "friendly",
  "storage": "s3",
  "generation_time_ms": 1234
}
```

### List Available Characters

```bash
curl http://localhost:5000/characters
```

### List Available Voices

```bash
curl http://localhost:5000/voices
```

### Get Character Details

```bash
curl http://localhost:5000/characters/assistant
```

---

## 🚢 Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    pip install Flask flask-cors boto3 python-dotenv

COPY . .

ENV PYTHONUNBUFFERED=1
ENV API_PORT=5000

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", \
     "--timeout", "120", "chatterbox.api_server:app"]
```

Build and run:

```bash
docker build -t chatterbox-tts .
docker run --gpus all -p 5000:5000 --env-file .env chatterbox-tts
```

### AWS EC2 Deployment

1. **Launch GPU instance** (g4dn.xlarge or g4dn.2xlarge)
2. **Install CUDA and dependencies**
3. **Clone and setup repository**
4. **Configure .env with AWS credentials**
5. **Create S3 bucket**: `python s3_manager.py create-bucket`
6. **Start with Gunicorn/Supervisor**

### Railway/Heroku Deployment

1. Set environment variables
2. Create `Procfile`: `web: gunicorn -b 0.0.0.0:$PORT --timeout 120 chatterbox.api_server:app`
3. Deploy

---

## 🧪 Testing

### Validate Configuration

```bash
python validate_config.py
```

Checks:
- Python dependencies
- AWS credentials
- S3 connection
- Character configuration
- API settings

### Run Integration Tests

```bash
python integration_test.py
```

Tests:
- Health check
- Character endpoints
- Voice endpoints
- Audio generation (base64)
- Audio generation (S3 URL)
- Audio generation (presigned URLs)
- Character voice switching

### Manual Testing

```bash
# Test base64 response
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","character":"narrator"}'

# Test S3 URL response
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","character":"narrator","return_format":"url"}'

# Test presigned URL
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","character":"narrator","return_format":"url","presigned":true}'
```

---

## 🔧 Frontend Integration

### React/Next.js Setup

```typescript
import { createTTSClient } from '@/lib/chatterbox-tts-client';

const ttsClient = createTTSClient(
  process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000'
);

// Generate audio for OpenRouter response
async function handleAIResponse(text: string, character: string = 'assistant') {
  const result = await ttsClient.generateAudio({
    text,
    character,
    returnFormat: 'url',
  });

  // Play audio
  const audio = new Audio(result.audio_url);
  audio.play();
}
```

### React Hook

```typescript
import { useChatterboxTTS } from '@/lib/chatterbox-tts-client';

function ChatComponent() {
  const { generateAudio, audioUrl, duration, isLoading, error } = 
    useChatterboxTTS(process.env.NEXT_PUBLIC_TTS_API_URL);

  return (
    <div>
      <button 
        onClick={() => generateAudio("Hello world", "narrator")}
        disabled={isLoading}
      >
        Generate Audio
      </button>
      
      {audioUrl && <audio src={audioUrl} controls />}
      {error && <p>Error: {error}</p>}
    </div>
  );
}
```

---

## 📊 S3 Management

### List Uploaded Audio

```bash
python s3_manager.py list
```

### Upload Manual Audio

```bash
python s3_manager.py upload /path/to/audio.wav
```

### AWS CLI Commands

```bash
# List bucket contents
aws s3 ls s3://chatterbox-audio-231399652064/chatterbox/audio/ --recursive

# Download audio
aws s3 cp s3://chatterbox-audio-231399652064/chatterbox/audio/file.wav ./

# Delete files
aws s3 rm s3://chatterbox-audio-231399652064/chatterbox/audio/ --recursive
```

---

## 🐛 Troubleshooting

### API won't start

**Error: "Import 'flask' could not be resolved"**

```bash
pip install Flask flask-cors
```

**Error: "CUDA out of memory"**

- Reduce `BATCH_SIZE` to 1
- Use CPU: Set `DEVICE=cpu` (will be slower)
- Restart API server to clear GPU memory

### S3 Connection Issues

**Error: "NoCredentialsError"**

- Check `.env` file has AWS credentials
- Verify credentials are not expired
- Test: `python test_s3_connection.py`

**Error: "Access Denied (403)"**

- Check IAM permissions include S3 access
- Verify bucket policy if using cross-account access

### Audio Generation Issues

**Error: "Model loading failed"**

- First request loads the model (takes 30-60s)
- Ensure sufficient GPU/CPU memory
- Check `LOG_LEVEL=DEBUG` for details

**Error: "Text too long"**

- Default max is 500 characters
- Modify `MAX_TEXT_LENGTH` in `.env`

### CORS Issues

**Error: "No 'Access-Control-Allow-Origin' header"**

- Update `CORS_ORIGINS` in `.env` to include your domain
- Ensure exact match (protocol + domain)

---

## 📈 Performance Optimization

### Enable Caching

```env
CACHE_ENABLED=true
CACHE_SIZE=100
```

Caches repeated audio generation (same text + character).

### GPU Optimization

```env
BATCH_SIZE=1
```

Adjust based on GPU memory (1-4 typically).

### S3 Performance

- Use CloudFront CDN for distributed delivery
- Enable S3 Transfer Acceleration
- Set lifecycle policies to delete old files

---

## 📝 API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Health check with GPU info |
| POST | `/generate-audio` | **Main OpenRouter endpoint** |
| POST | `/tts` | Generate audio file |
| POST | `/tts-json` | Generate with JSON response |
| GET | `/characters` | List all characters |
| GET | `/characters/{id}` | Get character details |
| POST | `/characters/{id}/voice` | Change character voice |
| GET | `/voices` | List all voices |
| GET | `/voices/{id}` | Get voice details |
| GET | `/languages` | List supported languages |

---

## 🔐 Security Considerations

1. **Credentials**
   - Never commit `.env` to git
   - Use IAM roles on EC2 instead of access keys
   - Rotate credentials regularly

2. **S3 Bucket**
   - Enable versioning
   - Set bucket policy to deny public upload
   - Use presigned URLs for temporary access
   - Enable encryption

3. **API**
   - Validate input length and format
   - Use HTTPS in production
   - Implement rate limiting
   - Monitor for abuse

---

## 📚 Additional Resources

- [S3_DEPLOYMENT_GUIDE.md](S3_DEPLOYMENT_GUIDE.md) - Detailed deployment guide
- [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md) - Frontend integration examples
- [AWS Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

---

## 🆘 Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Run `python validate_config.py` to check configuration
3. Check API logs: Set `LOG_LEVEL=DEBUG`
4. Run `python integration_test.py` for detailed test results

---

**Ready to deploy!** 🚀

Next steps:
1. Configure `.env` with your AWS credentials
2. Run `python validate_config.py` to verify setup
3. Start API: `python chatterbox/api_server.py`
4. Test with: `python integration_test.py`
5. Integrate with your Vercel frontend using the TypeScript client
