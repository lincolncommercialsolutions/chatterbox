# ✅ Active Deployment Checklist

Use this checklist to track your deployment progress. Check off items as you complete them.

## 🎯 Phase 1: Deploy API Server

### Railway Deployment (Recommended)
- [ ] Install Railway CLI: `npm install -g @railway/cli`
- [ ] Push code to GitHub
- [ ] Run `railway init` in project directory
- [ ] Connect GitHub account in Railway
- [ ] Run `railway up`
- [ ] Get API URL from Railway dashboard
- [ ] Test health endpoint: `curl https://your-api-url/health`
- [ ] API responds with healthy status

### Alternative: Render.com
- [ ] Go to render.com
- [ ] Create new Web Service
- [ ] Connect GitHub repo
- [ ] Set build command: `docker build -f Dockerfile.gpu -t chatterbox:latest .`
- [ ] Set start command: `python chatterbox/api_server.py`
- [ ] Copy environment variables from `.env`
- [ ] Deploy
- [ ] Get API URL from Render dashboard
- [ ] Test health endpoint

### Alternative: AWS
- [ ] Follow AWS_DEPLOYMENT_SETUP.md
- [ ] Launch EC2 instance (g4dn.xlarge or better)
- [ ] Configure security groups
- [ ] Push Docker image to ECR
- [ ] Create ECS task definition
- [ ] Create ECS service with load balancer
- [ ] Get load balancer DNS as API URL
- [ ] Test health endpoint

### Alternative: Local Server
- [ ] SSH into your server
- [ ] Clone repo: `git clone https://github.com/you/chatterbox.git`
- [ ] Configure `.env` with your credentials
- [ ] Run: `docker-compose up -d`
- [ ] Verify running: `docker ps | grep chatterbox`
- [ ] Test health endpoint

### Verification
- [ ] `curl $API_URL/health` returns status 200
- [ ] Response includes: `"status": "healthy"`
- [ ] GPU detection shows: `"device": "cuda"`
- [ ] Characters endpoint works: `curl $API_URL/characters`
- [ ] Voices endpoint works: `curl $API_URL/voices`

**Deployed API URL:** `https://________________`

---

## 🔗 Phase 2: Vercel Frontend Integration

### Environment Configuration
- [ ] Open Vercel project dashboard
- [ ] Go to Settings → Environment Variables
- [ ] Create variable: `NEXT_PUBLIC_TTS_API_URL`
- [ ] Value: `https://your-deployed-api-url.com`
- [ ] Apply to: All Environments (Development, Preview, Production)
- [ ] Save and redeploy Vercel project
- [ ] Verify in local `.env.local`: `NEXT_PUBLIC_TTS_API_URL=...`

### File Integration
- [ ] Create `lib/` directory in Vercel project
- [ ] Copy `chatterbox-tts-client.ts` to `lib/`
- [ ] Verify file exists: `ls lib/chatterbox-tts-client.ts`
- [ ] File compiles without TypeScript errors

### Service Module
- [ ] Create `lib/tts-service.ts`
- [ ] Import ChatterboxTTSClient
- [ ] Export ttsClient instance
- [ ] Create helper functions:
  - [ ] `generateAudioForMessage()`
  - [ ] `getCharacters()`
  - [ ] `getAvailableVoices()`
- [ ] No TypeScript errors
- [ ] Functions are exported and usable

### Testing Setup
- [ ] In browser console, test: `fetch($API_URL + '/health')`
- [ ] Response shows healthy status
- [ ] No CORS errors in browser console
- [ ] Network tab shows request succeeds

---

## 💬 Phase 3: Wire OpenRouter Integration

### Chat Component Setup
- [ ] Locate your chat message handler function
- [ ] Import TTS service: `import { generateAudioForMessage } from '@/lib/tts-service'`
- [ ] After OpenRouter response, capture:
  - [ ] Response text
  - [ ] Character ID (from context or props)
  - [ ] Optional: Voice ID override

### Audio Generation Integration
- [ ] Call `generateAudioForMessage(text, characterId)`
- [ ] Handle success: Get audio URL/blob
- [ ] Handle error: Log error, continue without audio
- [ ] Store audio data with message object

### Message State
- [ ] Add audio properties to message type:
  - [ ] `audioUrl?: string`
  - [ ] `audioBlob?: Blob`
  - [ ] `duration?: number`
  - [ ] `character: string`
- [ ] Update message display to include audio

### Testing
- [ ] Send test message in chat UI
- [ ] Verify OpenRouter response received
- [ ] Check network tab for TTS API call
- [ ] Verify TTS API returns audio data
- [ ] No errors in browser console

---

## 🎵 Phase 4: Audio Playback

### HTML Audio Element
- [ ] Create audio player in message component
- [ ] Set src to audio URL
- [ ] Add controls: play, pause, volume, timeline
- [ ] Handle audio loading states
- [ ] Handle audio errors

### Styling (Optional)
- [ ] Size audio player appropriately
- [ ] Match design with chat UI
- [ ] Mobile responsive
- [ ] Accessible controls

### Auto-Play (Optional)
- [ ] User enables auto-play in settings
- [ ] Audio plays automatically after generation
- [ ] User can disable if distracting

### Testing
- [ ] Audio element renders
- [ ] Play button works
- [ ] Volume control works
- [ ] Progress bar shows position
- [ ] Audio plays completely
- [ ] Audio duration displays correctly

---

## 🎨 Phase 5: Voice Selection (Optional)

### Character Selector
- [ ] Create character dropdown or list
- [ ] Load characters from API: `getCharacters()`
- [ ] Display character names
- [ ] Select default character
- [ ] Save user's selected character

### Voice Override (Optional)
- [ ] Create voice dropdown
- [ ] Load voices from API: `getAvailableVoices()`
- [ ] Allow user to pick specific voice
- [ ] Save voice preference

### Implementation
- [ ] Use as hook or provider for state
- [ ] Pass character/voice to message handler
- [ ] Regenerate audio if user changes character
- [ ] Show current character in chat header

### Testing
- [ ] Characters list loads and displays
- [ ] Selecting character updates messages
- [ ] Audio sounds different per character
- [ ] Voice selection works if implemented

---

## 🔒 Phase 6: CORS & Security

### CORS Configuration
- [ ] Get your Vercel app URL: `https://yourname.vercel.app`
- [ ] SSH to deployed API or update deployment
- [ ] Edit `.env` and update `CORS_ORIGINS`:
  ```env
  CORS_ORIGINS=https://yourname.vercel.app,https://www.yourname.vercel.app
  ```
- [ ] If custom domain, add that too
- [ ] Redeploy API with updated .env
- [ ] Wait for deployment to complete

### Testing CORS
- [ ] Open your Vercel app
- [ ] Open browser DevTools → Network tab
- [ ] Send a chat message
- [ ] Check TTS API request headers:
  - [ ] `Origin: https://yourname.vercel.app`
  - [ ] Response has `Access-Control-Allow-Origin`
  - [ ] No CORS errors in console

### Environment Security
- [ ] `OPENROUTER_API_KEY` is set in deployment
- [ ] AWS credentials are set in deployment
- [ ] No credentials in code (only in `.env`)
- [ ] No API keys logged to console
- [ ] Error messages don't reveal sensitive info

---

## 🧪 Phase 7: Testing & QA

### Health Checks
- [ ] API health endpoint responds
- [ ] GPU/device status shows correct device
- [ ] Cache status shows (if enabled)

### Character & Voice Endpoints
- [ ] `GET /characters` returns all characters
- [ ] Each character has required fields
- [ ] `GET /voices` returns all voices
- [ ] Each voice has required fields

### Audio Generation
- [ ] `POST /generate-audio` works
- [ ] Parameters: text, character, optional voice_id
- [ ] Returns audio in expected format
- [ ] Audio is playable
- [ ] Audio quality is acceptable

### Full Chat Flow
- [ ] User types message in Vercel app
- [ ] Message appears in chat
- [ ] Request sent to OpenRouter API
- [ ] OpenRouter returns response
- [ ] Response appears in chat
- [ ] TTS API called with response
- [ ] Audio generated and returned
- [ ] Audio player appears in message
- [ ] Audio plays from start to finish
- [ ] Audio quality matches expectations

### Error Handling
- [ ] API offline → graceful error message
- [ ] Invalid character → uses default
- [ ] Audio generation fails → shows retry button
- [ ] Network error → retry logic works
- [ ] No white screens or crashes

### Performance
- [ ] Audio generation takes < 10 seconds
- [ ] Typical generation time: 2-5 seconds
- [ ] Chat remains responsive
- [ ] Multiple quick messages don't break
- [ ] GPU cache improves repeated requests

### Cross-Device Testing
- [ ] Desktop Chrome → works
- [ ] Desktop Firefox → works
- [ ] Mobile Safari → works
- [ ] Mobile Chrome → works
- [ ] Tablet landscape → works
- [ ] Tablet portrait → works

---

## 🚀 Phase 8: Go Live

### Pre-Launch
- [ ] All tests pass
- [ ] No console errors
- [ ] Error handling tested
- [ ] Performance acceptable
- [ ] Monitoring/logging enabled
- [ ] Rollback plan prepared

### Launch Preparation
- [ ] Announce to users
- [ ] Set up error monitoring (optional: Sentry)
- [ ] Monitor API logs for errors
- [ ] Monitor S3 usage and costs
- [ ] Have support plan ready

### Day One Monitoring
- [ ] API uptime: 99%+ ✓
- [ ] Audio generation: < 5sec average
- [ ] User feedback: collecting
- [ ] Error rate: < 0.1%
- [ ] No CORS or auth issues

### Success Criteria
- [ ] Users can chat
- [ ] Each response generates audio
- [ ] Audio plays correctly
- [ ] Different characters sound different
- [ ] System stable for 24+ hours
- [ ] No critical errors

---

## 📊 Current Status

**Overall Progress:**
- [ ] Phase 1: Deploy API (ACTIVE)
- [ ] Phase 2: Vercel Integration
- [ ] Phase 3: OpenRouter Wiring
- [ ] Phase 4: Audio Playback
- [ ] Phase 5: Voice Selection
- [ ] Phase 6: CORS Setup
- [ ] Phase 7: Testing
- [ ] Phase 8: Go Live

**Completion:** ___% 

**Blockers:**
- [ ] None identified
- List any blockers here: _____________

**Notes:**
```
Add any notes about your deployment here
```

---

## 📞 Quick Reference

| Resource | Location |
|----------|----------|
| Quick Start | QUICK_DEPLOY_GUIDE.md |
| Full Guide | DEPLOYMENT_FINAL_STEPS.md |
| AWS Setup | AWS_DEPLOYMENT_SETUP.md |
| Frontend | FRONTEND_INTEGRATION.md |
| Voice System | VOICE_SYSTEM_GUIDE.md |
| API Testing | test_api.py |
| Config Template | .env.example |
| Voice Config | voices_config.json |

---

## 🎯 Key URLs & Credentials

**Deployed API URL:** 
```
https://________________
```

**Vercel Project:** 
```
https://________________.vercel.app
```

**S3 Bucket:** 
```
chatterbox-audio-231399652064
```

**OpenRouter API Key:** 
```
[Set in deployment environment]
```

---

**Last Updated:** [Your Date]
**Status:** Ready for Deployment
**Next Action:** Choose deployment platform and deploy API server

Good luck! 🚀
