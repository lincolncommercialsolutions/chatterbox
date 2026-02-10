# 🎛️ Chatterbox TTS Admin Interface

Complete web-based admin interface for managing voices, characters, and TTS settings.

## 🚀 Quick Access

**Admin Interface URL:** `http://localhost:5000/admin` (local) or `https://your-app.onrender.com/admin` (deployed)

Open in your browser and start managing your TTS system!

---

## 📋 Features

### 🎵 Voice Management
- **View all voices** with usage information
- **Upload new voice samples** to S3 automatically
- **Test voices** with live audio playback
- **Delete unused voices** (safety check prevents deletion if in use)
- Support for **WAV, MP3, FLAC** audio formats

### 🤖 Character Management  
- **View all characters** with their configurations
- **Create new characters** with custom parameters
- **Test character voices** with live audio generation
- **Delete characters** when no longer needed
- **Voice assignment** - assign any voice to any character

### ⚙️ Configuration
- **Real-time parameter tuning** with sliders
- **Language selection** for multilingual support
- **Color & emoji** customization for UI
- **System prompts** for character behavior
- **Generation parameters** (exaggeration, temperature, CFG weight)

---

## 🎯 Tab Overview

### Tab 1: 🎵 Voices
- **Voice Library** - Browse all available voices
- **Usage Information** - See which characters use each voice
- **Test Playback** - Generate and play sample audio
- **Delete Management** - Remove unused voices safely

### Tab 2: 🤖 Characters
- **Character Profiles** - View all configured characters
- **Voice Assignments** - See which voice each character uses
- **Parameter Display** - View generation settings
- **Test Generation** - Test character-specific audio output

### Tab 3: ⬆️ Upload Voice
- **File Upload** - Drag & drop or browse for audio files
- **Voice Configuration** - Set name, description, language
- **Tag Management** - Organize voices with custom tags
- **S3 Integration** - Automatic upload to your S3 bucket

### Tab 4: ✨ Create Character
- **Character Details** - Set name, description, system prompt
- **Voice Selection** - Choose from available voices
- **Parameter Tuning** - Adjust generation settings with real-time sliders
- **UI Customization** - Set emoji and color for the character

---

## 🔧 How to Use

### 1. **Add a New Voice**

1. Click **"⬆️ Upload Voice"** tab
2. **Drag & drop** your audio file (3-5 seconds, clear quality)
3. Enter **Voice ID** (e.g., `my_voice`) and **Name** (e.g., `My Custom Voice`)
4. Add **description** and **tags** for easy identification
5. Click **"⬆️ Upload Voice"**

**Result:** Voice is uploaded to S3 and ready to use immediately

### 2. **Create a Character Using Your Voice**

1. Click **"✨ Create Character"** tab  
2. Enter **Character ID** (e.g., `my_character`) and **Name**
3. **Select your uploaded voice** from the dropdown
4. **Adjust parameters**:
   - **Exaggeration** (0-1): How expressive the speech is
   - **Temperature** (0-1): How much variation in output
   - **CFG Weight** (0-1): How closely to follow the reference voice
5. Add **system prompt** for character behavior (optional)
6. Click **"✨ Create Character"**

**Result:** Character is created and available in your TTS API immediately

### 3. **Test Everything**

1. In **Voices** tab: Click **"🎵 Test"** on any voice
2. In **Characters** tab: Click **"🎵 Test"** on any character  
3. **Listen** to the generated audio to verify quality
4. **Adjust parameters** if needed by recreating the character

### 4. **Use in Your App**

```javascript
// Your character is now available in the API
const response = await fetch('/generate-audio', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: "Hello from my custom character!",
    character: "my_character"
  })
});
```

---

## 🛡️ Safety Features

### Voice Deletion Protection
- **Cannot delete voices** that are used by characters
- **Warning message** shows which characters would be affected
- **Must remove/reassign** characters first before deleting voice

### File Validation
- **Audio format checking** (WAV, MP3, FLAC only)
- **File size limits** prevent oversized uploads
- **Unique ID enforcement** prevents overwriting existing voices/characters

### Real-time Feedback
- **Live parameter updates** with sliders show exact values
- **Success/error messages** for all operations
- **Loading indicators** during audio generation

---

## 🎚️ Parameter Guide

### Voice Generation Parameters

| Parameter | Range | Effect | Recommended Values |
|-----------|-------|--------|-------------------|
| **Exaggeration** | 0.0 - 1.0 | Speech expressiveness | 0.4-0.6 (balanced), 0.7+ (very expressive) |
| **Temperature** | 0.0 - 1.0 | Output variation | 0.6-0.8 (natural), 0.9+ (creative) |
| **CFG Weight** | 0.0 - 1.0 | Voice adherence | 0.5-0.7 (balanced), 0.8+ (less strict) |

### Character Type Examples

**Professional Narrator:**
- Exaggeration: 0.3, Temperature: 0.5, CFG Weight: 0.8
- Tags: `professional`, `narrator`, `formal`

**Energetic Host:**
- Exaggeration: 0.8, Temperature: 0.9, CFG Weight: 0.4  
- Tags: `energetic`, `enthusiastic`, `casual`

**Calm Assistant:**
- Exaggeration: 0.5, Temperature: 0.7, CFG Weight: 0.6
- Tags: `calm`, `helpful`, `friendly`

---

## 🌐 Language Support

The admin interface supports all Chatterbox languages:

- **English** (en) - Primary
- **Spanish** (es)
- **French** (fr)  
- **German** (de)
- **Italian** (it)
- **Portuguese** (pt)
- **Polish** (pl)
- **Turkish** (tr)
- **Russian** (ru)
- **Dutch** (nl)
- **Czech** (cs)
- **Arabic** (ar)
- **Chinese Simplified** (zh-cn)
- **Japanese** (ja)
- **Hungarian** (hu)
- **Korean** (ko)

---

## 💾 Configuration Persistence

### Automatic Saving
- **All changes** are automatically saved to `character_voices.json`
- **No manual save** required - changes are immediate
- **Git-friendly format** - easy to version control

### File Locations
- **Configuration:** `/home/linkl0n/chatterbox/character_voices.json`
- **Uploaded Audio:** S3 bucket `chatterbox-audio-231399652064/chatterbox/voices/`
- **Local Fallback:** `/home/linkl0n/chatterbox/audio_samples/` (if S3 unavailable)

### Deployment Integration
- **Render.com:** Changes auto-deploy when you push to GitHub
- **Docker:** Restart container to reload configuration
- **Local:** No restart needed - changes are live immediately

---

## 🔍 API Endpoints

The admin interface uses these API endpoints (also available for programmatic access):

### Voice Management
```http
GET  /admin/voices                  # List all voices
POST /admin/upload-voice            # Upload new voice
POST /admin/test-voice/<voice_id>   # Test voice generation
DELETE /admin/delete-voice/<voice_id> # Delete voice
```

### Character Management  
```http
GET  /admin/characters                    # List all characters
POST /admin/create-character              # Create new character
DELETE /admin/delete-character/<char_id>  # Delete character
```

### Example API Usage
```bash
# Upload voice via API (if not using web interface)
curl -X POST http://localhost:5000/admin/upload-voice \
  -F "audio_file=@myvoice.wav" \
  -F "voice_id=api_voice" \
  -F "voice_name=API Voice" \
  -F "description=Uploaded via API"

# Create character via API
curl -X POST http://localhost:5000/admin/create-character \
  -H "Content-Type: application/json" \
  -d '{
    "character_id": "api_character",
    "character_name": "API Character", 
    "voice_id": "api_voice",
    "description": "Created via API"
  }'
```

---

## 🚨 Troubleshooting

### Upload Issues

**"S3 upload failed"**
- Check AWS credentials in `.env` file
- Verify S3 bucket permissions
- Ensure internet connection

**"File format not supported"**
- Use WAV, MP3, or FLAC files only
- Check file is not corrupted
- Try converting with audio software

### Generation Issues

**"Character not found"**
- Refresh the interface
- Check character was created successfully
- Restart server if running locally

**"Voice test failed"**
- Check model is loaded properly
- Verify GPU/CPU resources available
- Look at server logs for details

### Interface Issues

**"Failed to load voices/characters"**
- Check server is running correctly
- Verify API endpoints are responding
- Check browser console for errors

**"Upload button not working"**
- Check file is selected
- Verify all required fields filled
- Try refreshing the page

---

## 🎉 Success Examples

### Gaming Characters Setup
```
1. Upload warrior voice: "warrior.wav" → voice_id: "warrior"
2. Upload mage voice: "mage.wav" → voice_id: "mage" 
3. Create characters:
   - "warrior_tank" using "warrior" voice (exaggeration: 0.4, temp: 0.6)
   - "wise_mage" using "mage" voice (exaggeration: 0.5, temp: 0.7)
4. Test in your game chat system!
```

### Podcast Voices Setup
```
1. Upload host voice: "host.wav" → voice_id: "podcast_host"
2. Upload guest voice: "guest.wav" → voice_id: "podcast_guest"
3. Create characters:
   - "main_host" using "podcast_host" (professional settings)
   - "interview_guest" using "podcast_guest" (conversational settings)
4. Use in podcast generation pipeline!
```

### Multilingual Assistant
```
1. Upload English voice: "english.wav" → voice_id: "en_voice"
2. Upload Spanish voice: "spanish.wav" → voice_id: "es_voice"
3. Create characters:
   - "assistant_en" using "en_voice", language: "en"
   - "assistant_es" using "es_voice", language: "es"
4. Switch characters based on user language!
```

---

**🎯 Ready to create amazing voices!** 

Open `/admin` in your browser and start building your custom TTS characters. The intuitive interface makes voice management easy and powerful.

For questions or advanced configuration, see:
- [HOW_TO_ADD_VOICES.md](HOW_TO_ADD_VOICES.md) - Detailed voice setup guide
- [VOICE_MANAGEMENT.md](VOICE_MANAGEMENT.md) - Advanced voice system documentation