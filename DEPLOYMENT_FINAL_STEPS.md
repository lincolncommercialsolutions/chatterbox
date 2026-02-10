# Chatterbox TTS - Final Deployment & Integration Steps

Complete checklist to go from development to production with your Vercel frontend.

## ✅ Completed
- S3 Integration (connected and configured)
- Character Voice Definitions (character_voices.json)
- Voice-to-Character Mapping (api_server.py)
- TTS API Server (ready for deployment)
- Frontend Client Library (chatterbox-tts-client.ts)
- Integration Documentation

## 📋 Remaining Steps

### 1. Deploy the API Server

Choose your deployment platform:

#### Option A: Railway (Recommended - Easiest)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and create project
railway login
railway init

# Create railway.json
cat > railway.json << EOF
{
  "build": {
    "builder": "dockerfile",
    "dockerfile": "Dockerfile.gpu"
  }
}
EOF

# Deploy
railway up

# Get your API URL from the dashboard
# Example: https://chatterbox-tts.railway.app
```

#### Option B: Render.com
```bash
# 1. Push code to GitHub
git add .
git commit -m "Ready for deployment"
git push

# 2. Go to https://render.com
# 3. New → Web Service
# 4. Connect GitHub repo
# 5. Build command: docker build -f Dockerfile.gpu -t chatterbox-tts:latest .
# 6. Start command: python chatterbox/api_server.py
# 7. Environment variables (see below)
# 8. Deploy!
```

#### Option C: AWS ECS (Most Scalable)
```bash
# See AWS_DEPLOYMENT_SETUP.md for complete guide
# Includes: ECR push, task definition, service creation, load balancer

# Quick summary:
# 1. Push Docker image to ECR
# 2. Create ECS task definition
# 3. Create ECS service with load balancer
# 4. Get load balancer DNS as your API URL
```

#### Option D: Docker on Your Own Server
```bash
# On your server
git clone <your-repo>
cd chatterbox

# Configure environment
cp .env.example .env
nano .env  # Edit with your S3 credentials and settings

# Run with Docker Compose
docker-compose up -d

# Verify
curl http://localhost:5000/health
```

### 2. Environment Variables for Deployment

Set these in your deployment platform's environment settings:

```env
# API Configuration
API_PORT=5000
DEVICE=cuda  # Use 'cpu' if no GPU available
LOG_LEVEL=INFO

# Text Processing
MAX_TEXT_LENGTH=500
DEFAULT_MAX_TOKENS=400

# Caching
CACHE_ENABLED=true

# S3 Configuration (already configured)
S3_ENABLED=true
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_AUDIO_PREFIX=chatterbox/audio/
S3_VOICES_PREFIX=chatterbox/voices/

# CORS (UPDATE WITH YOUR DOMAIN)
CORS_ORIGINS=https://yourdomain.vercel.app,https://www.yourdomain.vercel.app

# Logging/Monitoring
SENTRY_DSN=  # Optional: error tracking
```

### 3. Get Your Deployed API URL

After deployment, you'll have a public URL:
- **Railway**: `https://your-project.railway.app`
- **Render**: `https://your-service.onrender.com`
- **AWS**: `https://chatterbox-api.your-domain.com` (with load balancer)
- **Custom**: Your server's domain

Save this URL - you'll need it in step 4.

---

## 🎯 Frontend Integration (Vercel)

### Step 1: Copy TTS Client to Vercel Project

```bash
# In your Vercel project root
mkdir -p lib
cp chatterbox-tts-client.ts lib/
```

### Step 2: Update Environment Variables

In your Vercel project `.env.local`:

```env
# Add this line with your deployed API URL from Step 3
NEXT_PUBLIC_TTS_API_URL=https://your-deployed-api.com

# Optional: for OpenRouter (if not already configured)
OPENROUTER_API_KEY=your-openrouter-key
```

### Step 3: Create TTS Service Module

Create `lib/tts-service.ts`:

```typescript
import { ChatterboxTTSClient } from './chatterbox-tts-client';

export const ttsClient = new ChatterboxTTSClient(
  process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000'
);

/**
 * Generate audio for a message
 */
export async function generateAudioForMessage(
  text: string,
  characterId: string = 'narrator'
): Promise<{ audioUrl: string; duration: number } | null> {
  try {
    const { url, duration, revoke } = await ttsClient.generatePlayableAudio({
      text,
      character: characterId,
    });

    // Auto-revoke after audio plays
    setTimeout(() => revoke(), duration * 1000 + 1000);

    return { audioUrl: url, duration };
  } catch (error) {
    console.error('Failed to generate audio:', error);
    return null;
  }
}

/**
 * Get available characters and voices
 */
export async function getAvailableCharacters() {
  try {
    return await ttsClient.getCharacters();
  } catch (error) {
    console.error('Failed to get characters:', error);
    return [];
  }
}

export async function getAvailableVoices() {
  try {
    return await ttsClient.getVoices();
  } catch (error) {
    console.error('Failed to get voices:', error);
    return [];
  }
}
```

### Step 4: Wire OpenRouter to TTS in Chat Component

Here's how to integrate OpenRouter responses with TTS:

```typescript
// pages/api/chat.ts (or your chat endpoint)
import { generateAudioForMessage } from '@/lib/tts-service';

export async function POST(req: NextRequest) {
  const { userMessage, characterId = 'narrator' } = await req.json();

  try {
    // 1. Get response from OpenRouter
    const openrouterResponse = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: userMessage }],
        system: `You are ${characterId}. Respond in character.`
      }),
    });

    const { choices } = await openrouterResponse.json();
    const aiResponse = choices[0].message.content;

    // 2. Generate audio for the response
    const audioData = await generateAudioForMessage(aiResponse, characterId);

    // 3. Return both text and audio
    return NextResponse.json({
      text: aiResponse,
      audio: audioData?.audioUrl || null,
      duration: audioData?.duration || 0,
      character: characterId,
    });

  } catch (error) {
    console.error('Chat error:', error);
    return NextResponse.json(
      { error: 'Failed to process chat' },
      { status: 500 }
    );
  }
}
```

### Step 5: Create Chat Component with Audio

Create `components/ChatWithAudio.tsx`:

```typescript
'use client';

import React, { useState, useRef } from 'react';
import { generateAudioForMessage, getAvailableCharacters } from '@/lib/tts-service';

interface Message {
  id: string;
  text: string;
  audioUrl?: string;
  duration?: number;
  character: string;
  role: 'user' | 'assistant';
}

export function ChatWithAudio() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedCharacter, setSelectedCharacter] = useState('narrator');
  const [isLoading, setIsLoading] = useState(false);
  const [characters, setCharacters] = useState<any[]>([]);
  const audioRefs = useRef<{ [key: string]: HTMLAudioElement }>({});

  // Load characters on mount
  React.useEffect(() => {
    getAvailableCharacters().then(setCharacters);
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      character: 'user',
      role: 'user',
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call your chat API endpoint
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userMessage: input,
          characterId: selectedCharacter,
        }),
      });

      const data = await response.json();

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.text,
        audioUrl: data.audio,
        duration: data.duration,
        character: selectedCharacter,
        role: 'assistant',
      };

      setMessages(prev => [...prev, aiMessage]);

      // Auto-play audio if available
      if (data.audio && audioRefs.current[aiMessage.id]) {
        audioRefs.current[aiMessage.id].play();
      }

    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      {/* Character Selector */}
      <select
        value={selectedCharacter}
        onChange={(e) => setSelectedCharacter(e.target.value)}
        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
      >
        {characters.map(char => (
          <option key={char.id} value={char.id}>
            {char.name}
          </option>
        ))}
      </select>

      {/* Messages */}
      <div style={{ 
        height: '400px', 
        overflowY: 'auto', 
        border: '1px solid #ccc', 
        marginBottom: '10px',
        padding: '10px'
      }}>
        {messages.map(msg => (
          <div
            key={msg.id}
            style={{
              marginBottom: '10px',
              padding: '10px',
              backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5',
              borderRadius: '4px',
            }}
          >
            <p>{msg.text}</p>
            
            {msg.audioUrl && (
              <audio
                ref={(el) => {
                  if (el) audioRefs.current[msg.id] = el;
                }}
                src={msg.audioUrl}
                controls
                style={{ width: '100%', marginTop: '5px' }}
              />
            )}
          </div>
        ))}
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Type your message..."
          style={{ flex: 1, padding: '8px' }}
          disabled={isLoading}
        />
        <button
          onClick={handleSendMessage}
          disabled={isLoading}
          style={{
            padding: '8px 16px',
            backgroundColor: '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer',
          }}
        >
          {isLoading ? 'Loading...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
```

### Step 6: Add Voice Selector UI (Optional)

For more advanced voice control, use the example component:

```bash
# Copy the example to your project
cp frontend/VoiceSelector.example.tsx components/
```

Then use it:

```typescript
import { VoiceAndCharacterSelector } from '@/components/VoiceSelector.example';

export default function Page() {
  return (
    <VoiceAndCharacterSelector 
      apiUrl={process.env.NEXT_PUBLIC_TTS_API_URL!}
      onAudioGenerated={(blob, duration) => {
        console.log(`Generated ${duration}s audio`);
      }}
    />
  );
}
```

### Step 7: Update CORS in Deployment

Make sure your API has the correct CORS setting for your Vercel domain:

```env
CORS_ORIGINS=https://yourdomain.vercel.app,https://www.yourdomain.vercel.app
```

If using custom domain on Vercel, add that too:
```env
CORS_ORIGINS=https://yourdomain.vercel.app,https://custom.yourdomain.com
```

---

## 🧪 Testing Checklist

### Local Testing (Before Deployment)

```bash
# 1. Start API locally
docker-compose up

# 2. Test health endpoint
curl http://localhost:5000/health

# 3. Test character list
curl http://localhost:5000/characters

# 4. Test audio generation
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Test","character":"narrator"}'

# 5. Test with Vercel frontend (update .env.local to use localhost:5000)
# Visit your local Vercel app and test chat
```

### Production Testing (After Deployment)

- [ ] API health check returns healthy status
- [ ] Can list characters: `GET /characters`
- [ ] Can get voices: `GET /voices`
- [ ] Audio generation works: `POST /generate-audio`
- [ ] Frontend can reach API (no CORS errors)
- [ ] Chat component sends message to OpenRouter
- [ ] OpenRouter returns response
- [ ] Audio is generated for response
- [ ] Audio plays in chat UI
- [ ] Voice selector works (change voices)

### Full Pipeline Test

1. **User sends message** → "Hello, how are you?"
2. **OpenRouter generates response** → "I'm doing well, thanks for asking!"
3. **TTS generates audio** → 2.3 seconds
4. **Audio plays** in chat UI automatically
5. **User can select different character** → Audio regenerates with different voice

---

## 🔧 Troubleshooting Deployment

### Issue: API not responding

```bash
# Check logs
docker-compose logs -f

# Check if port 5000 is exposed
docker ps | grep chatterbox

# Test locally
curl http://localhost:5000/health
```

### Issue: CORS errors from Vercel

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**: Update `CORS_ORIGINS` environment variable in your deployment

```bash
# Should include your Vercel domain
CORS_ORIGINS=https://yourdomain.vercel.app
```

Then redeploy with updated environment variable.

### Issue: S3 connection fails

**Error**: `Failed to connect to S3`

**Solution**: Check S3 credentials in environment variables

```bash
# Verify these are set:
S3_ENABLED=true
S3_BUCKET_NAME=your-bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Test connection:
curl http://localhost:5000/health | jq '.s3_enabled'
```

### Issue: Audio generation slow

**Solutions**:
1. Check GPU availability: `curl http://localhost:5000/health | jq '.gpu'`
2. Use smaller max_tokens: `"max_tokens": 200`
3. Check server CPU/memory usage
4. Consider upgrading instance type

### Issue: OpenRouter API errors

**Check**:
- OpenRouter API key is valid: `OPENROUTER_API_KEY`
- Model exists: `gpt-3.5-turbo` or your chosen model
- Account has credits
- Rate limits not exceeded

---

## 📊 Monitoring & Analytics

### Health Check Endpoint

```bash
# Monitor GPU, memory, cache status
curl https://your-api.com/health | jq

# Expected response:
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "gpu": {
    "cuda_available": true,
    "device": "Tesla V100",
    "memory_allocated": "4.2GB"
  },
  "cache_enabled": true,
  "cache_size": 23
}
```

### Logging

All requests are logged with:
- Timestamp
- Character ID
- Text length
- Generation time (ms)
- Duration (seconds)
- Errors/warnings

Access logs via:
- **Railway**: Railway dashboard → Logs tab
- **Render**: Render dashboard → Logs
- **AWS**: CloudWatch Logs
- **Docker**: `docker-compose logs -f`

### Performance Metrics

Track these KPIs:
- **Generation time**: Should be < 5 seconds
- **Cache hit rate**: % of repeated requests
- **GPU utilization**: Should use GPU when available
- **Memory usage**: Should stay under 80% of available

---

## 🚀 Going Live Checklist

Before telling users about your chatbot:

- [ ] API deployed and stable (24 hours uptime)
- [ ] CORS configured correctly
- [ ] OpenRouter API key active and funded
- [ ] S3 bucket backing up audio (optional)
- [ ] Error handling implemented (graceful fallback)
- [ ] Voice variety tested (multiple characters/voices)
- [ ] Audio quality acceptable
- [ ] Load testing done (expected user load)
- [ ] Monitoring/alerts set up
- [ ] Documentation updated
- [ ] Rollback plan prepared

---

## 📞 Quick Reference

| Component | Status | Location |
|-----------|--------|----------|
| API Server | Deployed | `https://your-api.com` |
| S3 Integration | Connected | AWS S3 Bucket |
| Vercel Frontend | Ready | `https://yourdomain.vercel.app` |
| Character Config | Ready | `character_voices.json` |
| TTS Client | Integrated | `lib/chatterbox-tts-client.ts` |
| Chat Component | Ready | `components/ChatWithAudio.tsx` |

---

## Next Steps

1. ✅ Choose deployment platform (Step 1)
2. ✅ Deploy API server
3. ✅ Get API URL from deployment
4. ✅ Update Vercel `.env.local`
5. ✅ Integrate TTS client in Vercel
6. ✅ Create chat component with audio
7. ✅ Wire OpenRouter to TTS
8. ✅ Test full pipeline
9. ✅ Go live! 🎉

**Need help?** Check the documentation files:
- `AWS_DEPLOYMENT_SETUP.md` - AWS-specific deployment
- `FRONTEND_INTEGRATION.md` - Frontend integration details
- `VOICE_SYSTEM_GUIDE.md` - Voice/character management
