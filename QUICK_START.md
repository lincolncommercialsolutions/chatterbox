# Chatterbox TTS with S3 - Quick Start Guide

**Complete setup for OpenRouter AI character voice synthesis with S3 audio storage on Vercel frontend.**

⏱️ **Setup Time: ~10 minutes**

---

## 🎯 What You Get

```
OpenRouter AI Response
        ↓
Chatterbox TTS API
        ↓
Audio Generation (GPU accelerated)
        ↓
S3 Upload
        ↓
Vercel Frontend plays audio
```

---

## 📦 Installation (2 minutes)

### 1. Install Dependencies

```bash
cd /home/linkl0n/chatterbox
pip install Flask flask-cors boto3 python-dotenv
```

Or use automated setup:

```bash
bash setup.sh
```

### 2. Verify Configuration

```bash
python validate_config.py
```

You should see:
```
✓ AWS credentials configured
✓ S3 bucket exists and is accessible
✓ Configuration is valid!
```

---

## 🚀 Start Using (3 minutes)

### Step 1: Start the API Server

```bash
python chatterbox/api_server.py
```

Wait for:
```
✓ Model loaded successfully
Chatterbox TTS API Server - AWS Production Deployment
```

### Step 2: Test with cURL

```bash
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world! I am your AI assistant.",
    "character": "assistant",
    "return_format": "url"
  }'
```

You'll get:
```json
{
  "success": true,
  "audio_url": "https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/chatterbox/audio/assistant/2026/02/09/hash.wav",
  "duration": 2.5,
  "character": "assistant"
}
```

### Step 3: Try Different Characters

```bash
# Narrator voice
curl -X POST http://localhost:5000/generate-audio \
  -d '{"text":"Story time!","character":"narrator","return_format":"url"}'

# Luna (mysterious)
curl -X POST http://localhost:5000/generate-audio \
  -d '{"text":"The mystery deepens...","character":"luna","return_format":"url"}'

# Sage (calm)
curl -X POST http://localhost:5000/generate-audio \
  -d '{"text":"Let us meditate.","character":"sage","return_format":"url"}'
```

---

## 🎭 Available Characters

| Character | Voice | Best For |
|-----------|-------|----------|
| **narrator** | narrator | Storytelling, narration |
| **assistant** | friendly | General conversations ⭐ |
| **luna** | mysterious | Engaging stories |
| **sage** | calm | Educational content |
| **echo** | expert | Technical topics |
| **zephyr** | energetic | Motivation & energy |

---

## 💻 Frontend Integration (3 minutes)

### Install TypeScript Client

```bash
# Copy to your Next.js project
cp frontend/chatterbox-tts-client.ts ./lib/
```

### Use in React/Next.js

```typescript
import { createTTSClient } from '@/lib/chatterbox-tts-client';

const ttsClient = createTTSClient('http://localhost:5000');

// Generate audio for OpenRouter response
async function handleAIResponse(text: string, character = 'assistant') {
  const result = await ttsClient.generateAudio({
    text,
    character,
    returnFormat: 'url',  // Gets S3 URL instead of base64
  });

  // Play the audio
  const audio = new Audio(result.audio_url);
  audio.play();
}
```

### React Hook

```typescript
import { useChatterboxTTS } from '@/lib/chatterbox-tts-client';

function ChatBot() {
  const { generateAudio, audioUrl, isLoading, error } = 
    useChatterboxTTS('http://localhost:5000');

  return (
    <div>
      <button 
        onClick={() => generateAudio("Hello!", "assistant")}
        disabled={isLoading}
      >
        Generate Audio
      </button>
      
      {audioUrl && <audio src={audioUrl} controls autoPlay />}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# AWS Credentials (already configured)
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1

# S3 Settings
S3_ENABLED=true
S3_BUCKET_NAME=chatterbox-audio-231399652064

# API Settings
API_PORT=5000
CORS_ORIGINS=http://localhost:3000,https://yourdomain.vercel.app

# Character Settings
DEFAULT_CHARACTER=assistant
```

### Character Voices (character_voices.json)

6 characters with customizable parameters:

```json
{
  "characters": {
    "assistant": {
      "name": "AI Assistant",
      "voice_id": "friendly",
      "description": "Friendly helper"
    },
    "narrator": {
      "name": "Narrator",
      "voice_id": "narrator",
      "description": "Professional storyteller"
    }
    // ... more characters
  }
}
```

Edit to add/modify characters!

---

## 🧪 Testing

### Run All Tests

```bash
python integration_test.py
```

Tests everything:
- ✓ API health
- ✓ Character loading
- ✓ Voice configuration
- ✓ Audio generation
- ✓ S3 upload
- ✓ Presigned URLs

### Manual Tests

```bash
# Health check
curl http://localhost:5000/health

# List characters
curl http://localhost:5000/characters

# List voices
curl http://localhost:5000/voices

# Generate audio (base64)
curl -X POST http://localhost:5000/generate-audio \
  -d '{"text":"Hello","character":"assistant"}'

# Generate audio (S3 URL)
curl -X POST http://localhost:5000/generate-audio \
  -d '{"text":"Hello","character":"assistant","return_format":"url"}'

# Generate with presigned URL (expires in 1 hour)
curl -X POST http://localhost:5000/generate-audio \
  -d '{"text":"Hello","character":"assistant","return_format":"url","presigned":true}'
```

---

## 🐛 Troubleshooting

### API won't start

**Error: "Module not found"**
```bash
pip install Flask flask-cors boto3 python-dotenv
```

**Error: "CUDA out of memory"**
```bash
# Edit .env
BATCH_SIZE=1
```

### S3 issues

**Error: "Access Denied"**
```bash
# Check credentials
python test_s3_connection.py

# Verify bucket exists
aws s3 ls | grep chatterbox-audio
```

**Error: "Bucket doesn't exist"**
```bash
python s3_manager.py create-bucket
```

### Audio generation slow

**First request takes 30-60s (model loading)**
- This is normal
- Cached in memory for subsequent requests

**Slow audio generation overall**
- Check GPU: `nvidia-smi`
- Enable caching: `CACHE_ENABLED=true`
- Reduce `BATCH_SIZE`

---

## 📚 Full Documentation

- **README_S3_SETUP.md** - Complete setup guide
- **S3_DEPLOYMENT_GUIDE.md** - Production deployment
- **IMPLEMENTATION_CHECKLIST.md** - What was implemented
- **SETUP_SUMMARY.md** - Technical summary

---

## 🚀 Deploy to Production

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    pip install Flask flask-cors boto3 python-dotenv
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "chatterbox.api_server:app"]
```

```bash
docker build -t chatterbox-tts .
docker run --gpus all -p 5000:5000 --env-file .env chatterbox-tts
```

### AWS EC2

```bash
# Launch g4dn.xlarge instance
# SSH into instance
cd /home/ubuntu/chatterbox

# Install dependencies
pip install -r requirements.txt
pip install Flask flask-cors boto3 python-dotenv

# Configure .env with AWS credentials
# Create S3 bucket
python s3_manager.py create-bucket

# Start with systemd or supervisor
python chatterbox/api_server.py
```

---

## 📊 API Reference

### POST /generate-audio

Main endpoint for OpenRouter integration.

**Request:**
```json
{
  "text": "Response text from OpenRouter",
  "character": "assistant",
  "return_format": "url",
  "presigned": false,
  "max_tokens": 400
}
```

**Response:**
```json
{
  "success": true,
  "audio_url": "https://...",
  "sample_rate": 24000,
  "duration": 2.5,
  "character": "assistant",
  "voice_id": "friendly",
  "storage": "s3"
}
```

### GET /health

Check API status and GPU.

### GET /characters

List available characters.

### GET /voices

List available voices.

### POST /characters/{characterId}/voice

Change character's voice.

---

## ⚡ Performance Tips

1. **Enable Caching**
   ```env
   CACHE_ENABLED=true
   CACHE_SIZE=100
   ```

2. **Use GPU**
   - Install CUDA
   - Automatic detection

3. **Batch Processing**
   - Generate multiple audios
   - System handles efficiently

4. **S3 CDN**
   - Use CloudFront for faster downloads
   - Presigned URLs for temp access

---

## 🔒 Security Checklist

- [x] AWS credentials in `.env` (not in code)
- [x] S3 bucket versioning enabled
- [x] Presigned URLs with expiration
- [x] Input validation
- [x] CORS properly configured

---

## 📈 What's Running

| Service | Port | Status |
|---------|------|--------|
| Chatterbox TTS API | 5000 | ✓ Running |
| S3 Audio Storage | Remote | ✓ Connected |
| Model (GPU/CPU) | Local | ✓ Loaded |

---

## ✨ Features

✅ GPU-accelerated text-to-speech
✅ 6 pre-configured characters
✅ S3 audio storage with CDN
✅ Presigned URLs for temporary access
✅ OpenRouter integration ready
✅ Full TypeScript client for frontend
✅ React hooks available
✅ Comprehensive error handling
✅ Audio caching
✅ Configurable parameters

---

## 🎯 Next Steps

1. ✓ Install dependencies
2. ✓ Verify configuration: `python validate_config.py`
3. ✓ Start API: `python chatterbox/api_server.py`
4. ✓ Test: `python integration_test.py`
5. → Integrate frontend TypeScript client
6. → Connect OpenRouter responses to TTS
7. → Deploy to production

---

## 💬 Support

- Run `python validate_config.py` to check setup
- Run `python test_s3_connection.py` for S3 issues
- Run `python integration_test.py` for full diagnostics
- Check logs with `LOG_LEVEL=DEBUG` in .env

---

**You're all set!** 🚀

The system is ready for use. Your Vercel frontend can now:
1. Get AI responses from OpenRouter
2. Generate audio with Chatterbox TTS
3. Play audio with character voices
4. Store audio on S3

Enjoy your voice-enabled chatbot!
