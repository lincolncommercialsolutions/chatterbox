# 🚀 Render.com Deployment Guide

## ✅ Prerequisites Complete
- ✅ GitHub repo: `https://github.com/lincolncommercialsolutions/chatterbox`
- ✅ Code is pushed to main branch
- ✅ Environment variables ready

---

## Step 1: Create New Web Service

1. Go to **[https://render.com](https://render.com)**
2. Click **"Sign Up"** or **"Log In"** (use GitHub login for easier integration)
3. Click **"New +"** button (top right)
4. Select **"Web Service"**

---

## Step 2: Connect GitHub Repository

1. Click **"Connect account"** under GitHub
2. Authorize Render to access your repositories
3. Find and select: **`lincolncommercialsolutions/chatterbox`**
4. Click **"Connect"**

---

## Step 3: Configure Service Settings

### Basic Settings:
- **Name:** `chatterbox-tts-api` (or any name you prefer)
- **Region:** Choose closest to your users (e.g., `Oregon (US West)`)
- **Branch:** `main`
- **Root Directory:** Leave blank

### Build Settings:
- **Runtime:** `Python 3`
- **Build Command:**
  ```bash
  chmod +x build.sh && bash build.sh
  ```

### Start Command:
```bash
chmod +x start.sh && bash start.sh
```

### Instance Type:
- **Free tier:** Available but limited (good for testing)
- **Starter ($7/month):** Recommended for production
- **Pro ($25+/month):** For GPU support (faster audio generation)

---

## Step 4: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add these variables one by one:

### Required Variables:

| Key | Value |
|-----|-------|
| `AWS_ACCESS_KEY_ID` | `your-aws-access-key-id` |
| `AWS_SECRET_ACCESS_KEY` | `your-aws-secret-access-key` |
| `AWS_REGION` | `us-east-1` |
| `S3_ENABLED` | `true` |
| `S3_BUCKET_NAME` | `chatterbox-audio-231399652064` |
| `S3_AUDIO_PREFIX` | `chatterbox/audio/` |
| `S3_VOICES_PREFIX` | `chatterbox/voices/` |
| `S3_PRESIGNED_URL_EXPIRY` | `3600` |
| `API_PORT` | `5000` |
| `API_HOST` | `0.0.0.0` |
| `LOG_LEVEL` | `INFO` |
| `CORS_ORIGINS` | `http://localhost:3000,https://*.vercel.app` |
| `MAX_TEXT_LENGTH` | `500` |
| `DEFAULT_MAX_TOKENS` | `400` |
| `BATCH_SIZE` | `1` |
| `CACHE_ENABLED` | `true` |
| `CACHE_SIZE` | `100` |
| `DEFAULT_CHARACTER` | `assistant` |
| `CHARACTER_CONFIG_FILE` | `character_voices.json` |

### Optional (if using OpenRouter):
| Key | Value |
|-----|-------|
| `OPENROUTER_API_KEY` | `your-openrouter-key` |

---

## Step 5: Deploy

1. Click **"Create Web Service"** at the bottom
2. Render will start building your app
3. Watch the **"Logs"** tab for progress
4. Wait for: `✓ Build successful` and `✓ Deploy live`

**Deployment takes:** ~5-10 minutes for first deploy

---

## Step 6: Get Your API URL

Once deployed, your URL will be shown at the top:

```
https://chatterbox-tts-api.onrender.com
```

**Copy this URL** - you'll need it for Vercel!

---

## Step 7: Test Your Deployment

### Test 1: Health Check
```bash
curl https://chatterbox-tts-api.onrender.com/health
```
**Expected:** `{"status": "healthy"}`

### Test 2: List Characters
```bash
curl https://chatterbox-tts-api.onrender.com/characters
```
**Expected:** JSON array with character list

### Test 3: Generate Audio
```bash
curl -X POST https://chatterbox-tts-api.onrender.com/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from Render!",
    "character": "assistant",
    "max_tokens": 400
  }'
```
**Expected:** JSON with audio URL or base64 data

---

## Step 8: Update Vercel Frontend

In your Vercel project:

### Add Environment Variable:
```env
NEXT_PUBLIC_TTS_API_URL = https://chatterbox-tts-api-bn7e.onrender.com

1. Go to Vercel Dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add `NEXT_PUBLIC_TTS_API_URL` with your Render URL
5. Click **"Save"**
6. Redeploy your Vercel app

---

## 🔧 Important Render.com Notes

### Free Tier Limitations:
- ⚠️ **Spins down after 15 minutes of inactivity**
- ⚠️ **First request after spin-down takes ~30-60 seconds**
- ⚠️ **750 hours/month free** (enough for 1 service)
- ✅ Good for testing and demos
- ❌ Not recommended for production

### Upgrading to Paid:
- **Starter ($7/month):** Always on, faster
- **Pro with GPU:** Better for audio generation performance

### Auto-Deploy:
- ✅ Enabled by default
- Every push to `main` branch triggers new deployment
- Check **"Logs"** tab to monitor deployments

---

## 📊 Monitoring Your Service

### Check Logs:
1. Go to Render Dashboard
2. Click on your service
3. Click **"Logs"** tab
4. Filter by errors: Click **"Error"** button

### Check Metrics:
1. Click **"Metrics"** tab
2. See: CPU, Memory, Request rate
3. Upgrade if hitting limits

---

## 🆘 Troubleshooting

### Build Failed
**Check logs for:**
- Missing dependencies in `requirements.txt`
- Python version mismatch
- File path issues

**Fix:** Update `requirements.txt` and push to GitHub

### Service Won't Start
**Common causes:**
- Wrong start command
- Missing environment variables
- Port configuration (should be 5000)

**Check:** Logs tab for specific error messages

### API Returns 502/503
**Causes:**
- Service is spinning up (free tier)
- App crashed
- Out of memory

**Fix:** Check logs, consider upgrading instance

### CORS Errors
**Fix:** Update `CORS_ORIGINS` environment variable to include your Vercel domain:
```
https://your-app.vercel.app,https://*.vercel.app
```

Then redeploy (or click "Manual Deploy" → "Deploy latest commit")

---

## 🎯 Next Steps

1. ✅ Deploy to Render (following steps above)
2. ✅ Test API endpoints
3. ✅ Copy API URL
4. ✅ Update Vercel environment variable
5. ✅ Test full integration (Vercel → Render API → S3 → audio playback)
6. 🎉 Go live!

---

## 💡 Pro Tips

- **Custom Domain:** Add in Render settings (free on paid plans)
- **Health Checks:** Render pings `/health` automatically
- **Secrets:** Use Render's secret files for large keys
- **Scaling:** Add more instances in settings (paid only)
- **Cron Jobs:** Keep free tier warm with external uptime monitor

---

## 📞 Resources

- **Render Dashboard:** https://dashboard.render.com
- **Render Docs:** https://render.com/docs
- **Support:** https://render.com/support

---

**Your service will be live at:**
`https://chatterbox-tts-api.onrender.com` (or your custom name)

Good luck! 🚀
