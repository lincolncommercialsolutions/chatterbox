# Vercel API Routes for Chatterbox TTS

These API routes should be placed in your Vercel/Next.js project to proxy requests to your EC2 TTS backend.

## Installation

### For Next.js App Router (Next.js 13+)

Copy the files to your Next.js project:

```bash
# Copy to your Next.js project
cp -r vercel-api-routes/api/* <your-nextjs-project>/app/api/
```

### For Next.js Pages Router (Next.js 12 and below)

```bash
# Copy to your Next.js project
cp -r vercel-api-routes/api/* <your-nextjs-project>/pages/api/
```

## Environment Variables

Add to your Vercel project environment variables:

```bash
TTS_API_URL=http://35.174.4.196:5000
```

### Setting in Vercel Dashboard

1. Go to your project in Vercel dashboard
2. Navigate to Settings → Environment Variables
3. Add new variable:
   - **Name**: `TTS_API_URL`
   - **Value**: `http://35.174.4.196:5000`
   - **Environments**: Production, Preview, Development

## API Endpoints

### POST /api/voice/tts

Generate TTS audio.

**Request:**
```json
{
  "text": "Hello world",
  "character": "andrew_tate",
  "language": "en",
  "max_tokens": 400
}
```

**Response (Success):**
```json
{
  "success": true,
  "audio": "base64_encoded_wav_data",
  "sample_rate": 24000,
  "duration": 2.5,
  "character_id": "andrew_tate"
}
```

**Response (Rate Limited - 429):**
```json
{
  "success": false,
  "error": "Server overloaded. Please retry in a few seconds.",
  "error_type": "rate_limit",
  "retry_after": 3
}
```

### GET /api/voice/health

Health check for TTS service.

**Response:**
```json
{
  "vercel": "healthy",
  "tts_backend": {
    "status": "healthy",
    "pool_size": 3,
    "available_models": 3
  },
  "api_url": "http://35.174.4.196:5000"
}
```

### GET /api/voice/characters

Get available TTS characters.

**Response:**
```json
{
  "characters": [
    {
      "id": "andrew_tate",
      "name": "Andrew Tate",
      "voice_id": "andrew_tate",
      "language": "en"
    }
  ]
}
```

## Features

- ✅ **Edge Runtime**: Fast, globally distributed
- ✅ **Timeout Handling**: 35s timeout with proper error messages
- ✅ **Rate Limit Passthrough**: 429 errors from EC2 passed to client
- ✅ **Caching**: 2-hour cache for successful responses
- ✅ **Error Handling**: Detailed error messages in development
- ✅ **CORS**: Automatic CORS handling by Vercel

## Troubleshooting

### Error: "FUNCTION_INVOCATION_FAILED"

This means the Vercel function crashed or timed out. Check:

1. **Timeout**: Increased to 60s with `maxDuration: 60`
2. **Runtime**: Using edge runtime for better performance
3. **Environment variable**: `TTS_API_URL` is set correctly

### Error: "Request timeout"

The EC2 server took longer than 35 seconds. This can happen when:

1. All 3 model instances are busy (queue is full)
2. Network issues between Vercel and EC2
3. EC2 server is overloaded

**Solution**: Frontend should retry after a few seconds.

### Testing

Test the API routes locally:

```bash
# In your Next.js project
npm run dev

# Test endpoints
curl -X POST http://localhost:3000/api/voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","character":"andrew_tate"}'

curl http://localhost:3000/api/voice/health
curl http://localhost:3000/api/voice/characters
```

## Production Checklist

- [ ] Environment variable `TTS_API_URL` set in Vercel
- [ ] API routes deployed to Vercel
- [ ] EC2 server is running and healthy
- [ ] Security group allows traffic from Vercel IPs (or use 0.0.0.0/0)
- [ ] Frontend updated to use `/api/voice/tts` instead of direct EC2 calls

## Security Notes

- **DO NOT** expose EC2 IP directly to frontend
- **Always** proxy through Vercel API routes
- **Consider** adding authentication to API routes if needed
- **Monitor** Vercel function logs for errors
