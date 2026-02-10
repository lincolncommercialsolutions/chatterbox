# 🎙️ How to Add Audio and Assign to Character

Quick guide to add custom voice audio samples and create new characters.

---

## 📋 Prerequisites

- Audio sample file (.wav, .flac, or .mp3)
- 3-5 seconds long
- Clear audio, no background noise
- Representative of desired voice quality

---

## 🚀 Method 1: Upload to S3 (Recommended)

### Step 1: Upload Your Audio File

```bash
# Make the script executable
chmod +x add_voice_guide.sh

# Run the upload script
./add_voice_guide.sh myvoice.wav my_voice_id "My Voice Name"

# Example:
./add_voice_guide.sh hero_voice.wav hero "Hero Voice"
```

**The script will:**
- Upload audio to S3: `s3://chatterbox-audio-231399652064/chatterbox/voices/`
- Generate the public URL
- Show you the config to add

### Step 2: Copy Output and Edit Config

The script outputs JSON config. Copy it and add to **`character_voices.json`**:

```json
{
  "voices": {
    "hero": {
      "name": "Hero Voice",
      "language": "en",
      "audio_url": "https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/chatterbox/voices/hero.wav",
      "description": "Energetic hero voice",
      "quality": "high",
      "tags": ["hero", "energetic", "custom"]
    }
  }
}
```

### Step 3: Create Character Using This Voice

Add a character in the same file:

```json
{
  "characters": {
    "hero_character": {
      "name": "Hero",
      "voice_id": "hero",
      "language": "en",
      "description": "Brave hero character",
      "system_prompt": "You are a brave hero. Speak confidently and inspiringly.",
      "metadata": {
        "emoji": "🦸",
        "color": "#FF6B6B"
      }
    }
  }
}
```

### Step 4: Deploy Changes

**If running locally:**
```bash
# Restart the container
docker-compose restart
```

**If deployed on Render:**
1. Commit and push changes:
   ```bash
   git add character_voices.json
   git commit -m "Add new hero voice and character"
   git push origin main
   ```
2. Render will auto-deploy in ~2-3 minutes

### Step 5: Test

```bash
# Replace with your API URL
API_URL="http://localhost:5000"  # or https://your-app.onrender.com

# List characters (should include your new one)
curl $API_URL/characters

# Generate audio with new character
curl -X POST $API_URL/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I am the hero character!",
    "character": "hero_character"
  }'
```

---

## 🌐 Method 2: Use External URL

If your audio is already hosted somewhere:

### Step 1: Get Audio URL

Make sure your audio file is publicly accessible:
- Google Cloud Storage: `https://storage.googleapis.com/...`
- Any web server: `https://yourdomain.com/audio/voice.wav`
- Dropbox, etc. (public link)

### Step 2: Add to character_voices.json

```json
{
  "voices": {
    "custom_voice": {
      "name": "Custom Voice",
      "language": "en",
      "audio_url": "https://yourdomain.com/voices/custom.wav",
      "description": "My custom voice",
      "quality": "high",
      "tags": ["custom"]
    }
  },
  "characters": {
    "custom_char": {
      "name": "Custom Character",
      "voice_id": "custom_voice",
      "language": "en",
      "description": "Character with custom voice"
    }
  }
}
```

### Step 3: Deploy (same as Method 1, Step 4)

---

## 📁 Method 3: Manual S3 Upload (AWS CLI)

### Upload directly with AWS CLI:

```bash
# Upload audio file
aws s3 cp myvoice.wav s3://chatterbox-audio-231399652064/chatterbox/voices/myvoice.wav \
  --region us-east-1 \
  --content-type "audio/wav"

# Get the URL
echo "https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/chatterbox/voices/myvoice.wav"
```

Then follow Method 2, Step 2 to add to config.

---

## 🎨 Complete Example: Add Gaming Characters

Let's add 3 gaming characters with different voices:

### 1. Upload Audio Files

```bash
./add_voice_guide.sh warrior.wav warrior "Warrior Voice"
./add_voice_guide.sh mage.wav mage "Mage Voice"
./add_voice_guide.sh rogue.wav rogue "Rogue Voice"
```

### 2. Edit character_voices.json

```json
{
  "voices": {
    "warrior": {
      "name": "Warrior Voice",
      "language": "en",
      "audio_url": "https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/chatterbox/voices/warrior.wav",
      "description": "Strong, commanding warrior voice",
      "quality": "high",
      "tags": ["warrior", "strong", "commanding"],
      "parameters": {
        "exaggeration": 0.4,
        "temperature": 0.6,
        "cfg_weight": 0.8
      }
    },
    "mage": {
      "name": "Mage Voice",
      "language": "en",
      "audio_url": "https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/chatterbox/voices/mage.wav",
      "description": "Wise, mystical mage voice",
      "quality": "high",
      "tags": ["mage", "mystical", "wise"],
      "parameters": {
        "exaggeration": 0.5,
        "temperature": 0.7,
        "cfg_weight": 0.6
      }
    },
    "rogue": {
      "name": "Rogue Voice",
      "language": "en",
      "audio_url": "https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/chatterbox/voices/rogue.wav",
      "description": "Sly, cunning rogue voice",
      "quality": "high",
      "tags": ["rogue", "cunning", "sly"],
      "parameters": {
        "exaggeration": 0.6,
        "temperature": 0.8,
        "cfg_weight": 0.5
      }
    }
  },
  "characters": {
    "warrior": {
      "name": "Warrior",
      "voice_id": "warrior",
      "language": "en",
      "description": "Strong warrior character",
      "system_prompt": "You are a brave warrior. Speak with confidence and authority.",
      "metadata": {
        "emoji": "⚔️",
        "color": "#C0392B"
      }
    },
    "mage": {
      "name": "Mage",
      "voice_id": "mage",
      "language": "en",
      "description": "Wise mage character",
      "system_prompt": "You are a wise mage. Share knowledge with mystical wisdom.",
      "metadata": {
        "emoji": "🧙",
        "color": "#8E44AD"
      }
    },
    "rogue": {
      "name": "Rogue",
      "voice_id": "rogue",
      "language": "en",
      "description": "Cunning rogue character",
      "system_prompt": "You are a cunning rogue. Be clever and witty.",
      "metadata": {
        "emoji": "🗡️",
        "color": "#34495E"
      }
    }
  }
}
```

### 3. Test Each Character

```bash
API_URL="http://localhost:5000"

# Test warrior
curl -X POST $API_URL/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text": "For honor and glory!", "character": "warrior"}'

# Test mage
curl -X POST $API_URL/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text": "The ancient scrolls reveal...", "character": "mage"}'

# Test rogue
curl -X POST $API_URL/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text": "I work better in the shadows.", "character": "rogue"}'
```

---

## ⚙️ Understanding Voice Parameters

When adding voices, you can tune generation parameters:

| Parameter | Range | Effect | Recommended |
|-----------|-------|--------|-------------|
| **exaggeration** | 0.0-1.0 | Speech expressiveness | 0.4-0.6 (balanced), 0.7+ (very expressive) |
| **temperature** | 0.0-1.0 | Variation/randomness | 0.6-0.8 (natural), 0.9+ (creative) |
| **cfg_weight** | 0.0-1.0 | Adherence to reference voice | 0.5-0.7 (balanced), 0.8+ (less strict) |

**Examples:**
- **Calm narrator:** `exaggeration: 0.3, temperature: 0.5, cfg_weight: 0.8`
- **Energetic host:** `exaggeration: 0.8, temperature: 0.9, cfg_weight: 0.4`
- **Professional assistant:** `exaggeration: 0.5, temperature: 0.7, cfg_weight: 0.6`

---

## 🔍 Troubleshooting

### Audio file not found
- Check S3 URL is publicly accessible
- Test URL in browser: `https://chatterbox-audio-231399652064.s3.us-east-1.amazonaws.com/...`
- Verify S3 bucket permissions

### Character not showing up
- Check JSON syntax (use `python -m json.tool character_voices.json`)
- Ensure you restarted/redeployed
- Check API logs for errors

### Audio sounds wrong
- Try different parameters (exaggeration, temperature, cfg_weight)
- Ensure audio sample is clear and 3-5 seconds
- Test with different text inputs

### Voice sounds same as another
- Verify `audio_url` is different for each voice
- Check that audio files are actually different
- Try increasing `cfg_weight` for more variation

---

## 📚 Related Documentation

- **[VOICE_MANAGEMENT.md](VOICE_MANAGEMENT.md)** - Complete voice system guide
- **[VOICE_SYSTEM_GUIDE.md](VOICE_SYSTEM_GUIDE.md)** - Architecture and API reference
- **[character_voices.json](character_voices.json)** - Current configuration file

---

## 🎯 Quick Reference

### File to edit:
```
/home/linkl0n/chatterbox/character_voices.json
```

### Upload script:
```bash
./add_voice_guide.sh <audio_file> <voice_id> "<voice_name>"
```

### API endpoints:
- `GET /voices` - List all voices
- `GET /characters` - List all characters
- `POST /generate-audio` - Generate with character/voice

### After changes:
```bash
# Local
docker-compose restart

# Render
git push origin main
```

---

**Ready to add your voices! 🎤**
