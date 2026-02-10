# Chatterbox Voice Management System - Quick Start Guide

## What's New

You can now:
✅ **Add new voices** - Define speaking styles without code changes  
✅ **Add new characters** - Create AI personalities  
✅ **Switch voices** - Assign different voices to characters  
✅ **Override voices** - Use different voice for a single request  
✅ **Manage everything** - Via JSON config file + API endpoints  

## Quick Example

### Add a New Voice (5 minutes)

1. **Prepare audio sample** (3-5 seconds, .wav or .flac)
   ```
   my_voice.wav  (or upload to S3)
   ```

2. **Edit `voices_config.json`**:
   ```json
   {
     "voices": {
       "my_voice": {
         "name": "My Custom Voice",
         "language": "en",
         "audio_url": "https://s3.amazonaws.com/voices/my_voice.wav",
         "description": "My unique voice",
         "quality": "high",
         "tags": ["custom"]
       }
     }
   }
   ```

3. **Restart API**:
   ```bash
   docker-compose restart
   ```

4. **Use the voice**:
   ```bash
   curl -X POST http://localhost:5000/generate-audio \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Hello with my new voice!",
       "character": "narrator",
       "voice_id": "my_voice"
     }'
   ```

### Add a New Character (5 minutes)

1. **Edit `voices_config.json`**:
   ```json
   {
     "characters": {
       "my_character": {
         "name": "My Character",
         "voice_id": "my_voice",
         "language": "en",
         "exaggeration": 0.6,
         "temperature": 0.8,
         "cfg_weight": 0.5,
         "description": "My unique character"
       }
     }
   }
   ```

2. **Restart API**:
   ```bash
   docker-compose restart
   ```

3. **Generate audio**:
   ```bash
   curl -X POST http://localhost:5000/generate-audio \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Hello, I am the new character!",
       "character": "my_character"
     }'
   ```

## Voice vs Character System

### Voices
- **What**: Audio samples defining a speaking style
- **File**: `voices_config.json` → `voices` section
- **Example**:
  ```json
  "friendly": {
    "name": "Friendly Voice",
    "audio_url": "s3://bucket/voices/friendly.wav",
    "description": "Warm and approachable"
  }
  ```

### Characters
- **What**: AI personalities with generation settings
- **File**: `voices_config.json` → `characters` section
- **References**: A voice from the voices section
- **Example**:
  ```json
  "assistant": {
    "name": "AI Assistant",
    "voice_id": "friendly",  // ← References the voice above
    "exaggeration": 0.6,
    "temperature": 0.8,
    "cfg_weight": 0.5
  }
  ```

## API Endpoints

### Voice Management
```bash
# List all voices
GET /voices

# Get voice details (and which characters use it)
GET /voices/{voice_id}

# List all characters
GET /characters

# Get character details (including current voice)
GET /characters/{character_id}

# Change character's voice
POST /characters/{character_id}/voice
Body: { "voice_id": "friendly" }
```

### Generate Audio
```bash
# Generate with character's default voice
POST /generate-audio
Body: {
  "text": "Hello world",
  "character": "narrator"
}

# Generate with voice override
POST /generate-audio
Body: {
  "text": "Hello world",
  "character": "narrator",
  "voice_id": "friendly"  # Use different voice
}
```

## Frontend Integration

### TypeScript Client (Updated)

```typescript
import { ChatterboxTTSClient } from '@/lib/chatterbox-tts-client';

const client = new ChatterboxTTSClient(apiUrl);

// Get available voices
const voices = await client.getVoices();

// Get character details
const character = await client.getCharacterDetails('narrator');

// Generate audio with voice override
const { blob, duration } = await client.generateAudioBlob({
  text: "Hello!",
  character: "narrator",
  voiceId: "friendly"  // Override voice
});
```

### React Component Example

See `frontend/VoiceSelector.example.tsx` for complete working example:

```bash
# Copy to your project
cp frontend/VoiceSelector.example.tsx ./components/
```

Usage:
```typescript
import { VoiceAndCharacterSelector } from '@/components/VoiceSelector.example';

export default function Page() {
  return (
    <VoiceAndCharacterSelector 
      apiUrl={process.env.NEXT_PUBLIC_TTS_API_URL}
    />
  );
}
```

## Parameter Guide

### Generation Parameters

When defining a character, you can control:

#### `exaggeration` (0.0 - 1.0)
- 0.3-0.4: Calm, measured (Sage)
- 0.5-0.6: Normal, balanced (Most characters)
- 0.7+: Expressive, energetic (Elara)

#### `temperature` (0.0 - 1.0)
- 0.6: Consistent, predictable
- 0.7-0.8: Natural variation (typical)
- 0.9+: High variation, unpredictable

#### `cfg_weight` (0.0 - 1.0)
- 0.5: Follow reference voice closely
- 0.6-0.7: Balanced (typical)
- 0.8+: Less adherence to voice, more creative

## Real-World Examples

### Example 1: Game Characters

```json
{
  "voices": {
    "warrior": {
      "name": "Warrior",
      "audio_url": "s3://voices/warrior.wav",
      "description": "Bold, powerful voice",
      "tags": ["warrior", "male"]
    },
    "mage": {
      "name": "Mage",
      "audio_url": "s3://voices/mage.wav",
      "description": "Mysterious, arcane voice",
      "tags": ["mage", "mysterious"]
    }
  },
  "characters": {
    "conan": {
      "name": "Conan",
      "voice_id": "warrior",
      "exaggeration": 0.7,
      "temperature": 0.8,
      "cfg_weight": 0.6
    },
    "merlin": {
      "name": "Merlin",
      "voice_id": "mage",
      "exaggeration": 0.5,
      "temperature": 0.7,
      "cfg_weight": 0.7
    }
  }
}
```

### Example 2: Customer Service

```json
{
  "characters": {
    "sales": {
      "name": "Sales Agent",
      "voice_id": "friendly",
      "exaggeration": 0.6,
      "temperature": 0.7,
      "cfg_weight": 0.6
    },
    "support": {
      "name": "Support Agent",
      "voice_id": "calm",
      "exaggeration": 0.4,
      "temperature": 0.6,
      "cfg_weight": 0.8
    }
  }
}
```

## File Locations

| File | Purpose |
|------|---------|
| `voices_config.json` | Define all voices and characters |
| `chatterbox/api_server.py` | API implementation |
| `frontend/chatterbox-tts-client.ts` | TypeScript client library |
| `frontend/VoiceSelector.example.tsx` | Example React component |
| `VOICE_MANAGEMENT.md` | Detailed documentation |

## Workflow

```
1. Define Voice in voices_config.json
        ↓
2. Define Character (reference voice)
        ↓
3. Restart API (docker-compose restart)
        ↓
4. Test: GET /characters, /voices
        ↓
5. Generate Audio: POST /generate-audio
        ↓
6. (Optional) Change character voice via API
        ↓
7. Deploy to production
```

## Testing Your Setup

### Test Voices Load
```bash
curl http://localhost:5000/voices | jq
```

### Test Characters Load
```bash
curl http://localhost:5000/characters | jq
```

### Test Generation
```bash
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test message",
    "character": "narrator"
  }' | jq '.duration'
```

### Test Voice Override
```bash
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Same character, different voice",
    "character": "narrator",
    "voice_id": "friendly"
  }' | jq '.voice_id'
```

### Test Change Character Voice
```bash
curl -X POST http://localhost:5000/characters/luna/voice \
  -H "Content-Type: application/json" \
  -d '{"voice_id": "friendly"}'
```

## Troubleshooting

### Voice Not Found
```
{"success": false, "error": "Unknown voice: my_voice"}
```

**Fix**:
- Check spelling in `voices_config.json`
- Make sure voice is in `voices` section (not `characters`)
- Restart API: `docker-compose restart`

### Character Not Found
```
{"success": false, "error": "Unknown character: my_character"}
```

**Fix**:
- Check spelling in `voices_config.json`
- Make sure character is in `characters` section
- Make sure referenced `voice_id` exists
- Restart API

### Audio Quality Issues

**Try**:
1. Check voice audio sample quality
2. Adjust parameters:
   - Increase `exaggeration` for more expressive
   - Decrease `cfg_weight` for more adherence to voice
   - Adjust `temperature` for more/less variation

### Configuration Not Loading

**Fix**:
1. Validate JSON syntax: `python -m json.tool voices_config.json`
2. Check file permissions
3. Verify file location: `/home/linkl0n/chatterbox/voices_config.json`
4. Restart: `docker-compose down && docker-compose up`

## Performance Tips

1. **Audio Quality** - Better source audio = better results
2. **Reuse Voices** - Have multiple characters share voices
3. **Cache Audio** - Same text + character = instant replay
4. **Test Locally** - Try voices before deployment

## Next Steps

1. ✅ **Read**: Check `VOICE_MANAGEMENT.md` for complete details
2. ✅ **Test**: Run examples in this guide
3. ✅ **Customize**: Add your own voices and characters
4. ✅ **Integrate**: Use TypeScript client in your frontend
5. ✅ **Deploy**: Push to production

## Reference

- **Detailed Guide**: `VOICE_MANAGEMENT.md`
- **React Example**: `frontend/VoiceSelector.example.tsx`
- **API Documentation**: In `chatterbox/api_server.py` docstrings
- **Configuration**: `voices_config.json`

## Quick Commands

```bash
# Restart API after changes
docker-compose restart

# View logs
docker-compose logs -f

# Test API
python test_api.py http://localhost:5000

# Get all voices (pretty printed)
curl http://localhost:5000/voices | jq

# Get all characters (pretty printed)
curl http://localhost:5000/characters | jq

# Generate test audio
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Test","character":"narrator"}' | jq '.duration'
```

---

**You're all set!** 🎉

Start by adding a voice or character to `voices_config.json`, restart the API, and generate some audio!
