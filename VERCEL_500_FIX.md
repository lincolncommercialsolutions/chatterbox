# Quick Fix for Vercel 500 Errors

## Your Current Error

```
❌ TTS API Error: Error: TTS API error: 500 - A server error has occurred
FUNCTION_INVOCATION_FAILED
cle1::2vrvg-1770853997081-c7ce70f0ce3e
```

## Root Cause

Your Vercel serverless function `/api/voice/tts` is either:
1. Missing or misconfigured
2. Timing out (default Vercel timeout is 10s for Hobby plan)  
3. Not handling errors properly from the EC2 backend

## Immediate Fix

### Step 1: Copy API Routes to Your Vercel Project

```bash
# Navigate to your Next.js/Vercel project
cd /path/to/your/vercel/project

# Copy the API routes (adjust path based on your structure)
# For App Router (Next.js 13+):
cp -r /home/linkl0n/chatterbox/vercel-api-routes/api/* ./app/api/

# OR for Pages Router (Next.js 12):
cp -r /home/linkl0n/chatterbox/vercel-api-routes/api/* ./pages/api/
```

### Step 2: Add Environment Variable in Vercel

1. Go to https://vercel.com/dashboard
2. Select your project (charcat.chat)
3. Go to **Settings** → **Environment Variables**
4. Add new variable:
   ```
   Name: TTS_API_URL
   Value: http://35.174.4.196:5000
   ```
5. Select all environments (Production, Preview, Development)
6. Click **Save**

### Step 3: Redeploy

```bash
# In your Vercel project
git add .
git commit -m "Add Vercel API routes for TTS"
git push

# Or use Vercel CLI
vercel --prod
```

### Step 4: Test

```bash
# Test the health endpoint
curl https://charcat.chat/api/voice/health

# Test TTS generation
curl -X POST https://charcat.chat/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Testing","character":"andrew_tate"}'
```

## Why This Fixes It

### ✅ Edge Runtime
- Default Vercel functions timeout in 10s (Hobby) or 60s (Pro)
- Edge runtime has 30s timeout and better global performance
- Our EC2 backend takes up to 30s for queued requests

### ✅ Proper Error Handling  
- Catches EC2 429 rate limits and passes them to frontend
- Handles timeouts gracefully with 504 status
- Detailed error logging for debugging

### ✅ Caching
- 2-hour cache for successful responses
- Reduces load on EC2 backend
- Faster response for repeated requests

## Troubleshooting

### Still Getting 500 Errors?

1. **Check Vercel Logs**:
   ```bash
   vercel logs --prod
   ```

2. **Verify Environment Variable**:
   ```bash
   # In Vercel dashboard, check that TTS_API_URL is set
   ```

3. **Test EC2 Backend Directly**:
   ```bash
   curl http://35.174.4.196:5000/health
   ```

### Getting Timeout Errors (504)?

This means your EC2 backend is overloaded. The frontend should:

1. Show user-friendly message
2. Retry after 3-5 seconds
3. Consider falling back to browser TTS

### Frontend Already Has Retry Logic

Your frontend code already has good retry logic:
```javascript
// From your logs:
[TTS] Generating: "(in a deep, confident voice) Ah, testing audio, hu..." 
      (andrew_tate) [attempt 1]
[TTS] ✗ Failed: TTS API error: 500 - Unknown error
// Falls back to legacy TTS
// Falls back to browser speech synthesis ✅
```

Once the API route is fixed, retries will work correctly.

## Expected Behavior After Fix

### Success (200):
```javascript
{
  "success": true,
  "audio": "UklGR...",  // Base64 WAV data
  "sample_rate": 24000,
  "duration": 2.5
}
```

### Rate Limited (429):
```javascript
{
  "success": false,
  "error": "Server overloaded. Please retry in a few seconds.",
  "error_type": "rate_limit",
  "retry_after": 3
}
```

### Timeout (504):
```javascript
{
  "success": false,
  "error": "Request timeout - TTS server is overloaded",
  "error_type": "timeout"
}
```

Your frontend's retry logic will handle these automatically! 🎉
