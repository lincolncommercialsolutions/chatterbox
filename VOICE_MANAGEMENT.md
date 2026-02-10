# Voice Management Guide - Chatterbox TTS

Complete guide for managing voices and characters in Chatterbox TTS API.

## Overview

Chatterbox supports a **two-tier voice system**:

1. **Voices** - Audio samples that define a speaking style
2. **Characters** - AI personalities that reference a voice and have generation parameters

This separation allows you to:
- Reuse the same voice for multiple characters
- Change a character's voice without recreating the character
- Easily add new voices and characters
- Test different voice/character combinations

## Voice System Architecture

```
Voices (Audio Samples)
├── narrator (Professional Narrator)
├── friendly (Friendly Voice)
├── expert (Expert Voice)
├── mysterious (Mysterious Voice)
├── calm (Calm Voice)
└── child (Child Voice)
        ↓ (referenced by)
Characters (AI Personalities)
├── narrator (uses "narrator" voice)
├── assistant (uses "friendly" voice)
├── expert (uses "expert" voice)
├── luna (uses "mysterious" voice)
├── sage (uses "calm" voice)
└── elara (uses "friendly" voice)
```

## API Endpoints for Voice Management

### List All Voices
```bash
GET /voices

Response:
{
  "voices": [
    {
      "id": "narrator",
      "name": "Professional Narrator",
      "language": "en",
      "description": "Clear, professional voice for narration",
      "quality": "high",
      "tags": ["professional", "formal", "narrative"]
    },
    ...
  ],
  "total": 6
}
```

### Get Voice Details
```bash
GET /voices/narrator

Response:
{
  "id": "narrator",
  "name": "Professional Narrator",
  "language": "en",
  "description": "Clear, professional voice for narration",
  "quality": "high",
  "tags": ["professional", "formal", "narrative"],
  "used_by_characters": ["narrator"]  # Which characters use this voice
}
```

### List All Characters
```bash
GET /characters

Response:
{
  "characters": [
    {
      "id": "narrator",
      "name": "Narrator",
      "language": "en",
      "description": "Professional narrator voice"
    },
    ...
  ],
  "total": 6
}
```

### Get Character Details
```bash
GET /characters/luna

Response:
{
  "id": "luna",
  "name": "Luna",
  "language": "en",
  "description": "Mysterious character voice",
  "voice_id": "mysterious",
  "parameters": {
    "exaggeration": 0.5,
    "temperature": 0.8,
    "cfg_weight": 0.6
  }
}
```

### Change Character's Voice
```bash
POST /characters/luna/voice

Request:
{
  "voice_id": "friendly"
}

Response:
{
  "success": true,
  "character": "luna",
  "voice_id": "friendly",
  "voice_name": "Friendly Voice"
}
```

### Generate Audio with Voice Override
```bash
POST /generate-audio

Request:
{
  "text": "Hello world",
  "character": "luna",
  "voice_id": "narrator"  # Override luna's default voice
}

Response:
{
  "success": true,
  "audio": "base64_encoded_wav...",
  "character": "luna",
  "voice_id": "narrator",  # Shows which voice was used
  "duration": 1.5,
  "generation_time_ms": 2345
}
```

## Adding New Voices

### Step 1: Prepare Voice Audio Sample

You need a short audio sample (.wav, .flac, or .mp3) that represents the voice. This should be:
- 3-5 seconds long
- Clear, without background noise
- Representative of how the voice should sound

### Step 2: Store the Audio File

Options:
- **S3 (Recommended for production)**
  ```
  s3://your-bucket/voices/my_voice.flac
  → URL: https://your-bucket.s3.amazonaws.com/voices/my_voice.flac
  ```

- **Local file (for development)**
  ```
  /app/voices/my_voice.flac
  → URL: /app/voices/my_voice.flac
  ```

- **Web URL**
  ```
  https://your-domain.com/audio/my_voice.wav
  ```

### Step 3: Add to voices_config.json

Edit `voices_config.json`:

```json
{
  "voices": {
    "my_voice": {
      "name": "My Voice Name",
      "language": "en",
      "audio_url": "https://s3.amazonaws.com/your-bucket/voices/my_voice.flac",
      "description": "Description of this voice",
      "quality": "high",
      "tags": ["tag1", "tag2"]
    }
  }
}
```

### Step 4: Restart API (or reload config)

```bash
# Restart the container
docker-compose restart

# Or if running directly
# Kill and restart the Python process
```

### Step 5: Verify

```bash
# Check voices list
curl http://localhost:5000/voices

# Get new voice details
curl http://localhost:5000/voices/my_voice

# Test audio generation with new voice
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test with my new voice",
    "character": "narrator",
    "voice_id": "my_voice"
  }'
```

## Adding New Characters

### Step 1: Choose or Create a Voice

The character must use an existing voice. Either:
- Use an existing voice (e.g., "friendly")
- Create a new voice first (see Adding New Voices above)

### Step 2: Add to voices_config.json

Edit `voices_config.json`:

```json
{
  "characters": {
    "my_character": {
      "name": "My Character Name",
      "voice_id": "friendly",        # Reference existing voice
      "language": "en",
      "exaggeration": 0.6,
      "temperature": 0.8,
      "cfg_weight": 0.5,
      "description": "Description of this character"
    }
  }
}
```

### Step 3: Understand Generation Parameters

- **exaggeration** (0-1): Controls how expressive/exaggerated the speech is
  - 0.3-0.4: Calm, measured (Sage)
  - 0.5-0.6: Normal, balanced (Most characters)
  - 0.7+: Expressive, energetic (Elara)

- **temperature** (0-1): Controls randomness/variation
  - 0.6: Consistent, predictable
  - 0.7-0.8: Natural variation
  - 0.9+: High variation, unpredictable

- **cfg_weight** (0-1): Classifier-free guidance strength
  - 0.5: Follow reference voice closely
  - 0.6-0.7: Balanced
  - 0.8+: Less adherence to voice, more creative

### Step 4: Restart and Test

```bash
# Restart container
docker-compose restart

# Verify character was added
curl http://localhost:5000/characters

# Test audio generation
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, I am the new character",
    "character": "my_character"
  }'
```

## Real-World Examples

### Example 1: Add Professional Corporate Voice

**Use case**: For a corporate AI assistant

```json
{
  "voices": {
    "corporate": {
      "name": "Corporate Professional",
      "language": "en",
      "audio_url": "https://s3.amazonaws.com/voices/corporate_sample.wav",
      "description": "Professional corporate spokesperson",
      "quality": "high",
      "tags": ["corporate", "professional", "business"]
    }
  },
  "characters": {
    "sales_bot": {
      "name": "Sales Bot",
      "voice_id": "corporate",
      "language": "en",
      "exaggeration": 0.4,
      "temperature": 0.6,
      "cfg_weight": 0.8,
      "description": "Professional sales representative"
    }
  }
}
```

### Example 2: Add Animated Character Voices

**Use case**: For a gaming/animation chatbot

```json
{
  "voices": {
    "hyper": {
      "name": "Hyper Energy",
      "language": "en",
      "audio_url": "https://s3.amazonaws.com/voices/hyper.wav",
      "description": "High-energy, excited voice",
      "quality": "high",
      "tags": ["energetic", "excited", "playful"]
    },
    "villain": {
      "name": "Villain Voice",
      "language": "en",
      "audio_url": "https://s3.amazonaws.com/voices/villain.wav",
      "description": "Menacing, dramatic voice",
      "quality": "high",
      "tags": ["dark", "dramatic", "villain"]
    }
  },
  "characters": {
    "hero": {
      "name": "Hero Character",
      "voice_id": "hyper",
      "language": "en",
      "exaggeration": 0.8,
      "temperature": 0.9,
      "cfg_weight": 0.5,
      "description": "Energetic hero protagonist"
    },
    "evil_wizard": {
      "name": "Evil Wizard",
      "voice_id": "villain",
      "language": "en",
      "exaggeration": 0.6,
      "temperature": 0.7,
      "cfg_weight": 0.7,
      "description": "Menacing antagonist"
    }
  }
}
```

### Example 3: Multiple Languages

**Use case**: For multilingual chatbot

```json
{
  "voices": {
    "spanish_narrator": {
      "name": "Spanish Narrator",
      "language": "es",
      "audio_url": "https://s3.amazonaws.com/voices/spanish_narrator.wav",
      "description": "Professional Spanish voice",
      "quality": "high",
      "tags": ["spanish", "professional"]
    }
  },
  "characters": {
    "spanish_character": {
      "name": "Spanish Character",
      "voice_id": "spanish_narrator",
      "language": "es",
      "exaggeration": 0.5,
      "temperature": 0.7,
      "cfg_weight": 0.6,
      "description": "Spanish language character"
    }
  }
}
```

## Frontend Integration

### Change Character Voice at Runtime

```typescript
import { ChatterboxTTSClient } from '@/lib/chatterbox-tts-client';

const ttsClient = new ChatterboxTTSClient(apiUrl);

// Get available voices
const voices = await ttsClient.getCharacters();

// Generate audio with voice override
const audio = await ttsClient.generateAudio({
  text: "Same character, different voice!",
  character: "luna",
  voice_id: "narrator"  // Override Luna's voice temporarily
});
```

### Voice Selection UI

```typescript
export function VoiceSelector({ character, onVoiceChange }) {
  const [voices, setVoices] = useState([]);

  useEffect(() => {
    // Load available voices
    const loadVoices = async () => {
      const response = await fetch('/api/voices');
      const data = await response.json();
      setVoices(data.voices);
    };
    loadVoices();
  }, []);

  return (
    <select onChange={(e) => onVoiceChange(e.target.value)}>
      <option value="">Default Voice</option>
      {voices.map(voice => (
        <option key={voice.id} value={voice.id}>
          {voice.name}
        </option>
      ))}
    </select>
  );
}
```

## Managing voices_config.json

### Configuration File Location

```
/home/linkl0n/chatterbox/voices_config.json
```

### When to Edit

Edit this file when:
- Adding new voices
- Adding new characters
- Changing default voice assignments
- Adjusting generation parameters

### Configuration Reload

```bash
# Option 1: Restart container
docker-compose restart

# Option 2: If using Python API directly
# Modify the VOICE_LIBRARY and CHARACTER_VOICES dicts and restart

# Option 3: Add dynamic reload endpoint (future enhancement)
```

### Validation

After editing, validate JSON syntax:

```bash
# Using Python
python -m json.tool voices_config.json

# Or use online JSON validator
```

## Monitoring Voice Usage

### Check Voice Usage

```bash
# Get which characters use a specific voice
curl http://localhost:5000/voices/friendly

# Response shows:
{
  "id": "friendly",
  "used_by_characters": ["assistant", "elara"]
}
```

### Get Character Voice Configuration

```bash
# Get full character details including voice
curl http://localhost:5000/characters/luna

# Shows:
{
  "voice_id": "mysterious",
  "parameters": {
    "exaggeration": 0.5,
    "temperature": 0.8,
    "cfg_weight": 0.6
  }
}
```

## Troubleshooting

### Issue: Voice Not Found

```
Error: Unknown voice: my_voice
```

**Solution**:
- Check spelling in voices_config.json
- Verify voice was added to VOICE_LIBRARY section
- Restart API server
- Verify with: `curl http://localhost:5000/voices`

### Issue: Audio Quality Poor

**Solutions**:
- Check voice audio sample quality
- Try adjusting `cfg_weight` (higher = less adherence to voice)
- Adjust `exaggeration` and `temperature` parameters
- Ensure audio file is accessible (check URL)

### Issue: Same Character, Different Voices

```bash
# This works! Temporarily use different voice
curl -X POST http://localhost:5000/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test",
    "character": "luna",
    "voice_id": "calm"  # Override voice for this request only
  }'
```

## Best Practices

1. **Voice Sample Quality**
   - Use clear, noise-free audio samples
   - 3-5 seconds duration
   - Representative of desired output

2. **Character Organization**
   - Reuse voices across multiple characters
   - Use consistent naming conventions
   - Document character personalities

3. **Parameter Tuning**
   - Start with defaults (0.5-0.7 range)
   - Test before deploying
   - Adjust based on listening tests

4. **Scaling**
   - Keep number of voices manageable (< 20)
   - Cache audio responses
   - Monitor API performance

5. **Backup**
   - Keep voices_config.json in version control
   - Back up audio files to S3
   - Document custom voices

## Advanced: Dynamic Voice Loading

Future enhancement to load voices from files:

```python
# Pseudo-code for future implementation
def load_voices_from_config(config_path: str):
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    global VOICE_LIBRARY, CHARACTER_VOICES
    VOICE_LIBRARY.update(config.get('voices', {}))
    CHARACTER_VOICES.update(config.get('characters', {}))
```

## Summary

The voice management system provides:

✅ **Flexible voice selection** - Choose different voices for each character  
✅ **Easy additions** - Add voices/characters without code changes  
✅ **Runtime overrides** - Temporarily use different voice for a request  
✅ **Voice reuse** - Multiple characters can share same voice  
✅ **Parameter control** - Fine-tune generation characteristics  

Start with default voices, then customize as needed for your use case!
