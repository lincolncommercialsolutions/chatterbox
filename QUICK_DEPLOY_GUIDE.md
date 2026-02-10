# 🚀 Quick Deployment Guide

Your Chatterbox TTS system is **ready to deploy**! Here's the fastest path to production.

## ✅ Current Status

**Already Configured:**
- ✅ API Server (api_server.py) - Full featured
- ✅ S3 Integration - Connected to `chatterbox-audio-231399652064`
- ✅ Voice System - 6 voices, 6 characters, fully configurable
- ✅ Docker Setup - GPU-ready Dockerfile and docker-compose
- ✅ Frontend Client - TypeScript client ready for Vercel
- ✅ CORS Setup - Ready for Vercel deployment
- ✅ Environment - All variables configured

**Status:** 🟢 Ready for deployment

---

## 1️⃣ Deploy API Server (Choose One)

### Option A: Railway (⭐ Recommended - Easiest)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Create GitHub repo and push code (Railway needs GitHub access)
git init
git add .
git commit -m "Ready to deploy to Railway"
git branch -M main
git remote add origin https://github.com/lincolncommercialsolutions/chatterbox.git
git push -u origin main

# 3. Login to Railway and deploy
railway login
cd /home/linkl0n/chatterbox
railway init
railway up

# 4. Get your API URL from Railway dashboard
# Example: https://chatterbox-prod-xxxxx.railway.app
```

**Result:** You'll get a URL like `https://chatterbox-prod-xxxxx.railway.app`

### Option B: Render.com (Free tier available)

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. **Settings:**
   - Build command: `docker build -f Dockerfile.gpu -t chatterbox:latest .`
   - Start command: `python chatterbox/api_server.py`
   - Environment: Copy variables from your `.env`
   - Select GPU instance (if paid plan)
5. Deploy!

**Result:** You'll get a URL like `https://chatterbox-prod.onrender.com`

### Option C: AWS EC2 (Most scalable)

Follow the detailed guide: [AWS_DEPLOYMENT_SETUP.md](AWS_DEPLOYMENT_SETUP.md)

**Result:** You'll get a URL like `https://chatterbox-api.yourdomain.com`

### Option D: Run on your own server

```bash
# On your server
cd /home/chatterbox
git clone https://github.com/YOUR_USERNAME/chatterbox.git
cd chatterbox

# Make sure Docker is installed
docker --version
docker-compose --version

# Start the service
docker-compose up -d

# Verify it's running
curl http://localhost:5000/health
```

**Result:** You'll get a URL like `http://your-server-ip:5000`

---

## 2️⃣ After Deployment - Get Your API URL

Once deployed, test your API:

```bash
# Replace with your actual deployed URL
API_URL="https://your-deployed-url.com"

# Test health endpoint
curl $API_URL/health

# Test character list
curl $API_URL/characters

# Test audio generation
curl -X POST $API_URL/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test",
    "character": "assistant",
    "max_tokens": 400
  }'
```

**Expected response:** Audio file (base64 encoded or S3 URL)

**Save this URL** - you'll need it in the next step!

---

## 3️⃣ Integrate with Vercel Frontend

### Step 1: Add Environment Variable

In your Vercel project (or locally in `.env.local`):

```env
# .env.local (for local development)
NEXT_PUBLIC_TTS_API_URL=https://your-deployed-api.com

# In Vercel Dashboard: Settings → Environment Variables
# Name: NEXT_PUBLIC_TTS_API_URL
# Value: https://your-deployed-api.com
# Select: All Environments
```

**Test it works:**
```bash
# In your Vercel project
curl $NEXT_PUBLIC_TTS_API_URL/health
```

### Step 2: Copy TTS Client

```bash
# Copy from chatterbox project to your Vercel project
mkdir -p lib
cp /home/linkl0n/chatterbox/frontend/chatterbox-tts-client.ts lib/

# Verify it's there
ls -la lib/chatterbox-tts-client.ts
```

### Step 3: Create TTS Service Module

Create `lib/tts-service.ts` in your Vercel project:

```typescript
import { ChatterboxTTSClient } from './chatterbox-tts-client';

const apiUrl = process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000';
console.log('TTS API URL:', apiUrl);

export const ttsClient = new ChatterboxTTSClient(apiUrl);

export async function generateAudioForMessage(
  text: string,
  characterId: string = 'assistant'
) {
  try {
    console.log(`Generating audio for: "${text.substring(0, 50)}..." with character: ${characterId}`);
    
    const result = await ttsClient.generateAudio({
      text,
      character: characterId,
    });
    
    console.log('Audio generated successfully');
    return result;
  } catch (error) {
    console.error('Audio generation failed:', error);
    return null;
  }
}

export async function getCharacters() {
  try {
    const chars = await ttsClient.getCharacters();
    console.log('Fetched characters:', chars.map(c => c.id).join(', '));
    return chars;
  } catch (error) {
    console.error('Failed to fetch characters:', error);
    return [];
  }
}
```

### Step 4: Wire Chat Component

In your chat component, whenever OpenRouter returns a response:

```typescript
// Example: In your message sending function
async function sendMessage(userMessage: string, character: string = 'assistant') {
  try {
    // 1. Get OpenRouter response
    const response = await fetch('/api/openrouter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage, character }),
    });
    
    const { text } = await response.json();
    
    // 2. Generate audio from TTS
    const audioData = await generateAudioForMessage(text, character);
    
    // 3. Add message to chat with audio
    setMessages(prev => [...prev, {
      text,
      audio: audioData?.url,
      audioBlob: audioData?.blob,
      character,
      role: 'assistant',
    }]);
    
  } catch (error) {
    console.error('Chat error:', error);
  }
}
```

### Step 5: Play Audio in UI

In your message display component:

```typescript
// Display message with audio player
function ChatMessage({ message }) {
  return (
    <div className="message">
      <p>{message.text}</p>
      
      {message.audio && (
        <audio controls className="message-audio">
          <source src={message.audio} type="audio/wav" />
          Your browser does not support audio.
        </audio>
      )}
    </div>
  );
}
```

---

## 4️⃣ Test Full Pipeline

```bash
# 1. Test API is accessible
curl https://your-deployed-api.com/health

# 2. In your Vercel app console, test:
fetch('https://your-deployed-api.com/characters')
  .then(r => r.json())
  .then(console.log)

# 3. Send a message in chat UI
# → Should call OpenRouter
# → Should generate audio
# → Should play audio

# 4. Change character (if you have selector)
# → Audio should sound different
```

---

## 🔧 Configuration Summary

### Environment Variables Set ✅

| Variable | Value | Purpose |
|----------|-------|---------|
| `S3_ENABLED` | `true` | Use S3 for audio storage |
| `S3_BUCKET_NAME` | `chatterbox-audio-231399652064` | S3 bucket for audio files |
| `AWS_REGION` | `us-east-1` | AWS region for S3 |
| `API_PORT` | `5000` | Flask app port |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed domains |
| `OPENROUTER_API_KEY` | `[your-key]` | OpenRouter API access |
| `DEFAULT_CHARACTER` | `assistant` | Default voice character |

### Character Voice Mapping ✅

| Character | Voice | Description |
|-----------|-------|-------------|
| `narrator` | narrator | Clear, professional |
| `assistant` | friendly | Warm, approachable |
| `expert` | expert | Authoritative |
| `luna` | mysterious | Enigmatic |
| `sage` | calm | Soothing |
| `elara` | friendly | Warm |

**To customize:** Edit `voices_config.json`

---

## 📋 Pre-Deployment Checklist

Before going live:

- [ ] API deployed and responding at your URL
- [ ] `curl https://your-api.com/health` returns `{"status": "healthy"}`
- [ ] NEXT_PUBLIC_TTS_API_URL set in Vercel
- [ ] TTS client copied to Vercel project
- [ ] Chat component sends messages to OpenRouter
- [ ] Audio generation called after OpenRouter response
- [ ] Audio plays in chat UI
- [ ] No CORS errors in browser console
- [ ] Different characters produce different voices
- [ ] Error handling works (no dead app on errors)

---

## 🆘 Quick Troubleshooting

### API not responding
```bash
# Check if API is running
curl https://your-deployed-api.com/health

# If 404: Your deployment didn't work
# Check your deployment platform's logs
# Railway: https://railway.app → Logs tab
# Render: https://render.com → Logs
```

### CORS errors in browser
```
Access to XMLHttpRequest from 'https://yourdomain.vercel.app'
blocked by CORS policy
```

**Fix:** Update CORS_ORIGINS in your deployed API:
```env
CORS_ORIGINS=https://yourdomain.vercel.app,https://www.yourdomain.vercel.app
```

Then redeploy the API.

### Audio not generating
```bash
# Test API audio generation
curl -X POST https://your-api.com/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test",
    "character": "assistant"
  }'

# If error: Check API logs for details
```

### Characters not loading
```typescript
// In your Vercel project console:
import { ttsClient } from '@/lib/tts-service';
const chars = await ttsClient.getCharacters();
console.log(chars);  // Should show list
```

---

## 📞 Documentation Files

For more detailed info:

- **[DEPLOYMENT_FINAL_STEPS.md](DEPLOYMENT_FINAL_STEPS.md)** - Complete deployment guide with all platforms
- **[AWS_DEPLOYMENT_SETUP.md](AWS_DEPLOYMENT_SETUP.md)** - AWS-specific detailed guide
- **[FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)** - Frontend integration details
- **[VOICE_SYSTEM_GUIDE.md](VOICE_SYSTEM_GUIDE.md)** - Voice/character customization

---

## 🎯 Next Actions (In Order)

1. **Pick deployment platform** (Railway recommended)
2. **Deploy API** using platform's instructions
3. **Copy API URL** from deployed app
4. **Update Vercel .env.local** with `NEXT_PUBLIC_TTS_API_URL`
5. **Copy TTS client** to Vercel project
6. **Create TTS service** module in `lib/tts-service.ts`
7. **Wire chat component** to call TTS after OpenRouter
8. **Test full pipeline** (message → OpenRouter → TTS → audio)
9. **Go live!** 🎉

---

## 💡 Pro Tips

- **Test locally first:** Keep `NEXT_PUBLIC_TTS_API_URL=http://localhost:5000` when developing
- **Use docker-compose:** Great for testing before cloud deployment
- **Cache is enabled:** Audio generation is faster on repeated requests
- **S3 storage:** Audio files are automatically backed up to S3
- **Monitor costs:** Watch S3 usage and API compute time
- **Scale up GPU:** If generation is slow, upgrade instance type

---

**Questions?** Check the docs or review examples:
- Complete example component: `frontend/VoiceSelector.example.tsx`
- API testing script: `test_api.py`
- Example characters: `voices_config.json`

You're ready! 🚀
